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
import tempfile
import unittest
from unittest import mock

from ccpi.web_viewer.trame_viewer import TrameViewer


class TrameViewerTest(unittest.TestCase):
    def setUp(self):
        # Get the head data
        self.head_path = os.path.join(sys.prefix, 'share','cil', 'head.mha')
        self.file_list = [self.head_path]
        self.trame_viewer = TrameViewer(mock.MagicMock, self.file_list)
        self.viewer_class = self.trame_viewer.cil_viewer
        pass

    def test_trame_viewer_init_throws_when_list_of_files_is_none(self):
        with self.assertRaises(ValueError) as cm:
            TrameViewer(mock.MagicMock, None)
        self.assertEqual(str(cm.exception), "list_of_files cannot be None as we need data to load in the viewer!")

    def test_trame_viewer_init(self):
        pass
