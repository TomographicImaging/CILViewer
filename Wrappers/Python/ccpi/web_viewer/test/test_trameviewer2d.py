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
import os
import sys
import unittest
from unittest import mock

from ccpi.web_viewer.trame_viewer2D import TrameViewer2D


class TrameViewer2DTest(unittest.TestCase):
    @mock.patch("ccpi.web_viewer.trame_viewer2D.CILViewer2D")
    @mock.patch("ccpi.web_viewer.trame_viewer.vtk")
    @mock.patch("ccpi.web_viewer.trame_viewer.TrameViewer.update_slice_data")
    def setUp(self, _, vtk_module, cil_viewer):
        # Get the head data
        self.head_path = os.path.join(sys.prefix, 'share', 'cil', 'head.mha')
        self.file_list = [self.head_path, "other_file_path_dir/other_file"]

        # add the cil_viewer and defaults for a default __init__
        self.cil_viewer = cil_viewer
        self.map_range = [0, 3790]
        self.cil_viewer.getSliceMapRange.return_value = self.map_range

        self.trame_viewer = TrameViewer2D(self.file_list)

    def test_create_drawer_ui_elements_constructs_each_of_the_ui_elements(self):
        pass
