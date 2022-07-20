#
#   Copyright 2022 STFC, United Kingdom Research and Innovation
#
#   Author 2022 Samuel Jones
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import unittest
from unittest import mock

from ccpi.web_viewer.web_app import arg_parser, reset_viewer2d, data_finder, set_viewer2d, main, change_orientation, change_opacity_mapping


class WebAppTest(unittest.TestCase):

    def setUp(self):
        reset_viewer2d()

    @mock.patch("ccpi.web_viewer.web_app.print")
    @mock.patch("ccpi.web_viewer.web_app.sys")
    def test_arg_parser_handles_h(self, sys, print_output):
        help_string = "web_app.py [optional args: -h, -d] <data_files>\n" \
                      "Args:\n" \
                      "-h: Show this help and exit the program\n" \
                      "-d, --2D: Use the 2D viewer instead of the 3D viewer, the default is to just use the 3D viewer."
        sys.argv = ["python_file.py", "-h"]
        arg_parser()

        print_output.assert_called_once_with(help_string)

    @mock.patch("ccpi.web_viewer.web_app.print")
    @mock.patch("ccpi.web_viewer.web_app.sys")
    def test_arg_parser_handles_2d(self, sys, print_output):
        from ccpi.web_viewer.web_app import VIEWER_2D
        self.assertEqual(VIEWER_2D, False)
        sys.argv = ["python_file.py", "--2D"]
        arg_parser()

        from ccpi.web_viewer.web_app import VIEWER_2D
        self.assertEqual(VIEWER_2D, True)
        print_output.assert_not_called()

    @mock.patch("ccpi.web_viewer.web_app.print")
    @mock.patch("ccpi.web_viewer.web_app.sys")
    def test_arg_parser_handles_d(self, sys, print_output):
        from ccpi.web_viewer.web_app import VIEWER_2D
        self.assertEqual(VIEWER_2D, False)
        sys.argv = ["python_file.py", "-d"]
        arg_parser()

        from ccpi.web_viewer.web_app import VIEWER_2D
        self.assertEqual(VIEWER_2D, True)
        print_output.assert_not_called()

    @mock.patch("ccpi.web_viewer.web_app.print")
    @mock.patch("ccpi.web_viewer.web_app.sys")
    def test_arg_parser_does_not_do_anything_with_unused_args(self, sys, print_output):
        sys.argv = ["python_file.py", "file/path/to/path"]
        arg_parser()

        print_output.assert_called_once_with(
            "This arg: file/path/to/path is not a valid file or directory. Assuming it is for trame.")

    @mock.patch("ccpi.web_viewer.web_app.os")
    @mock.patch("ccpi.web_viewer.web_app.print")
    @mock.patch("ccpi.web_viewer.web_app.sys")
    def test_data_finder_handles_directory_that_was_passed(self, sys, print_output, os):
        sys.argv = ["python_file.py", "dir/path/to/path"]
        os.listdir.return_value = ["path/to/file1.txt", "path/to/file2.txt"]
        os.path.isfile.return_value = False
        os.path.isdir.return_value = True
        os.path.join.return_value = "path/to/file1.txt"

        return_value = data_finder()

        os.listdir.assert_called_once_with("dir/path/to/path")
        print_output.assert_not_called()
        self.assertEqual(return_value, ["path/to/file1.txt", "path/to/file1.txt"])

    @mock.patch("ccpi.web_viewer.web_app.os")
    @mock.patch("ccpi.web_viewer.web_app.print")
    @mock.patch("ccpi.web_viewer.web_app.sys")
    def test_data_finder_handles_file_that_was_passed(self, sys, print_output, os):
        sys.argv = ["python_file.py", "/path/to/file.txt"]
        os.path.isfile.return_value = True
        os.path.isdir.return_value = True

        return_value = data_finder()

        print_output.assert_not_called()
        self.assertEqual(return_value, ["/path/to/file.txt"])

    @mock.patch("ccpi.web_viewer.web_app.os")
    @mock.patch("ccpi.web_viewer.web_app.print")
    @mock.patch("ccpi.web_viewer.web_app.sys")
    def test_data_finder_handles_multiple_passed_args(self, sys, print_output, os):
        sys.argv = ["python_file.py", "path/to/file1.txt", "path/to/file2.txt"]
        os.listdir.return_value = ["path/to/file1.txt", "path/to/file2.txt"]
        os.path.isfile.return_value = True
        os.path.isdir.return_value = False
        os.path.join.return_value = "path/to/file1.txt"

        return_value = data_finder()

        print_output.assert_not_called()
        self.assertEqual(return_value, ["path/to/file1.txt", "path/to/file2.txt"])

    @mock.patch("ccpi.web_viewer.web_app.arg_parser")
    @mock.patch("ccpi.web_viewer.web_app.TrameViewer2D")
    @mock.patch("ccpi.web_viewer.web_app.TrameViewer3D")
    def test_main_creates_trame_viewer_2d_when_VIEWER_2D_is_true(self, viewer3d, viewer2d, arg_parser):
        set_viewer2d(True)
        data_files = mock.MagicMock()
        arg_parser.return_value = data_files

        main()

        viewer3d.assert_not_called()
        viewer2d.assert_called_once_with(data_files)
        viewer2d.return_value.start.assert_called_once()

    @mock.patch("ccpi.web_viewer.web_app.arg_parser")
    @mock.patch("ccpi.web_viewer.web_app.TrameViewer2D")
    @mock.patch("ccpi.web_viewer.web_app.TrameViewer3D")
    def test_main_creates_trame_viewer_3d_when_VIEWER_2D_is_false(self, viewer3d, viewer2d, arg_parser):
        set_viewer2d(False)
        data_files = mock.MagicMock()
        arg_parser.return_value = data_files

        main()

        viewer3d.assert_called_once_with(data_files)
        viewer3d.return_value.start.assert_called_once()
        viewer2d.assert_not_called()

    @mock.patch("ccpi.web_viewer.web_app.TRAME_VIEWER")
    def test_change_orientation_orientation_not_kwargs_calls_nothing(self, trame_viewer):
        change_orientation()

        trame_viewer.switch_to_orientation.assert_not_called()

    @mock.patch("ccpi.web_viewer.web_app.TRAME_VIEWER")
    def test_change_orientation_is_not_an_int_gets_cast_to_int_before_passed(self, trame_viewer):
        change_orientation(orientation="0")

        trame_viewer.switch_to_orientation.assert_called_once_with(0)

    @mock.patch("ccpi.web_viewer.web_app.TRAME_VIEWER")
    def test_change_opacity_mapping_not_kwargs_calls_nothing(self, trame_viewer):
        change_opacity_mapping()

        trame_viewer.set_opacity_mapping.assert_not_called()
