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

from ccpi.web_viewer.trame_viewer import TrameViewer


class TrameViewerTest(unittest.TestCase):
    def setUp(self):
        # Get the head data
        self.head_path = os.path.join(sys.prefix, 'share', 'cil', 'head.mha')
        self.file_list = [self.head_path]
        self.trame_viewer = TrameViewer(mock.MagicMock, self.file_list)
        self.viewer_class = self.trame_viewer.cil_viewer

    def test_trame_viewer_init_throws_when_list_of_files_is_none(self):
        with self.assertRaises(ValueError) as cm:
            TrameViewer(mock.MagicMock, None)
        self.assertEqual(str(cm.exception), "list_of_files cannot be None as we need data to load in the viewer!")

    def test_trame_viewer_default_file_selects_head_by_default(self):
        pass

    def test_trame_viewer_default_file_select_first_in_list_if_no_head(self):
        pass

    def test_trame_viewer_loads_default_file_initially(self):
        pass

    def test_load_file_properly_uses_load_nexus_for_nexus_files(self):
        pass

    def test_load_file_does_not_load_nexus_for_none_nexus_files(self):
        pass

    def test_model_selector_list_is_generated_from_list_of_files(self):
        pass

    def test_model_create_model_selector_starts_with_default_file(self):
        pass

    def test_create_background_color_list_generate_properly(self):
        pass

    def test_create_background_selector_defaults_to_miles_blue(self):
        pass

    def test_create_slice_slider_min_max_default(self):
        pass

    def test_create_toggle_details_button_starts_false(self):
        pass

    def test_create_orientation_radio_buttons_has_3_orientations_and_defaults_to_XY(self):
        pass

    def test_construct_slice_window_slider_uses_percentage_when_cmax_less_than_100(self):
        pass

    def test_construct_slice_window_slider_does_not_use_percentage_when_cmax_more_than_100(self):
        pass

    def test_construct_slice_level_slider_uses_percentage_when_cmax_less_than_100(self):
        pass

    def test_construct_slice_level_slider_does_not_use_percentage_when_cmax_more_than_100(self):
        pass

    def test_construct_slice_window_range_slider_uses_percentage_when_cmax_less_than_100(self):
        pass

    def test_construct_slice_window_range_slider_does_not_use_percentage_when_cmax_more_than_100(self):
        pass

    def test_update_slice_data_raises_error(self):
        pass

    def test_update_slice_slider_data_updates_max_slice_and_default_slice(self):
        pass

    def test_change_background_changes_background_color_in_cil_viewer(self):
        pass

    def test_switch_orientation_calls_change_orientation_in_cil_viewer(self):
        pass

    # Ensure the defaults are updated
    def test_switch_orientation_calls_update_slice_slider_data(self):
        pass

    def test_switch_orientation_remakes_the_slice_slider(self):
        pass

    def test_switch_orientation_flushes_the_layout_after_renamking_the_slice_slider(self):
        pass

    def test_switch_orientation_updates_cil_viewer_pipeline(self):
        pass

    def test_change_window_level_detail_sliders_sets_window_and_level_defaults_for_slices(self):
        pass

    def test_change_slice_window_range_raises_error(self):
        pass

    def test_change_slice_window_raises_error(self):
        pass

    def test_change_slice_level_raises_error(self):
        pass

    def test_change_slice_number_raises_error(self):
        pass

    def test_construct_drawer_layout_raises_error(self):
        pass
    
    def test_create_drawer_ui_elements_raises_error(self):
        pass

    def test_show_slice_histogram_will_set_the_state_of_histogramPlotActor(self):
        pass