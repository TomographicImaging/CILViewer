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

from ccpi.web_viewer.trame_viewer3D import TrameViewer3D


class TrameViewer3DTest(unittest.TestCase):
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

        self.trame_viewer = TrameViewer3D(self.file_list)

    def test_create_drawer_ui_elements_constructs_each_of_the_ui_elements(self):
        pass

    @mock.patch("ccpi.web_viewer.trame_viewer3D.vuetify.VCol")
    @mock.patch("ccpi.web_viewer.trame_viewer3D.vuetify.VRow")
    @mock.patch("ccpi.web_viewer.trame_viewer3D.vuetify.VContainer")
    @mock.patch("ccpi.web_viewer.trame_viewer3D.vuetify.VDivider")
    def test_construct_drawer_layout_sets_layout_children(self, v_divider, v_container, v_row, v_col):
        pass

    def test_create_reset_defaults_button(self):
        pass

    def test_construct_show_slice_histogram_switch(self):
        pass

    def test_create_reset_camera_button(self):
        pass

    def test_create_clipping_toggle(self):
        pass

    def test_create_clipping_removal_button(self):
        pass

    def test_create_color_choice_selector(self):
        pass

    def test_create_opacity_radio_buttons(self):
        pass

    def test_create_toggle_volume_visibility(self):
        pass

    def test_create_toggle_slice_visibility(self):
        pass

    def test_construct_color_slider(self):
        pass

    def test_construct_windowing_slider(self):
        pass

    def test_update_windowing_defaults_calls_update_slice_data(self):
        pass

    def test_update_windowing_defaults_does_not_update_slice_data_if_no_slice_window_range_slider(self):
        pass

    def test_update_windowing_defaults_does_not_update_slice_data_if_slide_window_present_but_slice_window_range_slider_is_false(self):
        pass

    def test_update_windowing_defaults_updates_level_window_sliders_if_slice_window_range_slider_present(self):
        pass

    def test_load_files_calls_super_class(self):
        pass

    def test_load_file_updates_slice_slider_data(self):
        pass

    def test_load_file_updates_windowing_defaults(self):
        pass

    def test_load_file_saves_a_new_camera_position(self):
        pass

    def test_switch_render_calls_toggle_volume_visibility(self):
        pass

    def test_switch_slice_toggles_visibility_correctly(self):
        pass

    def test_change_color_map_passes_cmap_to_setVolumeColorMapName(self):
        pass

    def test_change_windowing_percentage_and_scalar(self):
        pass

    def test_change_windowing_percentage_and_gradient(self):
        pass

    def test_change_windowing_not_percentage_and_scalar(self):
        pass

    def test_change_windowing_not_percentage_and_gradient(self):
        pass

    def test_reset_cam_only_calls_adjust_camera_without_original_cam_data_or_html_view(self):
        pass

    def test_reset_cam_copies_camera_data_if_original_cam_data_is_set(self):
        pass

    def test_reset_cam_updates_html_view_if_html_view_is_set(self):
        pass

    def test_set_default_button_state_sets_correct_defaults(self):
        pass

    def test_set_default_button_state_sets_visibility_of_the_slice(self):
        pass

    def test_set_default_button_state_sets_visibility_of_the_volume(self):
        pass

    def test_set_default_button_state_removes_clipping_planes_if_present(self):
        pass

    def test_set_default_button_state_removes_clipping_planes_if_clipping_plane_initialised_is_True(self):
        pass

    def test_change_coloring_percentage(self):
        pass

    def test_change_coloring_not_percentage(self):
        pass

    def test_change_window_level_detail_sliders(self):
        pass

    def test_change_slice_visibility_if_visibility_true(self):
        pass

    def test_change_slice_visibility_if_visibility_false(self):
        pass

    def test_change_volume_visibility_if_visibility_true(self):
        pass

    def test_change_volume_visibility_if_visibility_false(self):
        pass

    def test_change_clipping_false(self):
        pass

    def test_change_clipping_true(self):
        pass

    def test_remove_clipping_plane_where_planew_is_not_set_does_nothing(self):
        pass

    def test_remove_clipping_plane_where_planew_is_set(self):
        pass

    def test_show_slice_histogram_where_show_histogram_is_true(self):
        pass

    def test_show_slice_histogram_where_show_histogram_is_false(self):
        pass

    def test_update_sice_data(self):
        pass
