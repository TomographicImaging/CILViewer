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
from unittest.mock import call

from ccpi.web_viewer.trame_viewer3D import TrameViewer3D


class TrameViewer3DTest(unittest.TestCase):
    # This test has the potential to be flaky on minor version numbers of trame, due to private API usage.
    def check_vuetify_default(self, object_to_check, expected_default):
        self.assertEqual(object_to_check._py_attr["v_model"][1], expected_default)

    @mock.patch("ccpi.web_viewer.trame_viewer3D.CILViewer")
    @mock.patch("ccpi.web_viewer.trame_viewer.vtk")
    @mock.patch("ccpi.web_viewer.trame_viewer.TrameViewer.update_slice_data")
    def setUp(self, _, vtk_module, cil_viewer):
        # Get the head data
        self.head_path = os.path.join(sys.prefix, 'share', 'cil', 'head.mha')
        self.file_list = [self.head_path, "other_file_path_dir/other_file"]

        # add the cil_viewer and defaults for a default __init__
        self.cil_viewer = cil_viewer
        self.map_range = [0, 3790]
        self.cil_viewer.getVolumeMapRange.return_value = self.map_range
        self.cil_viewer.getSliceMapRange.return_value = self.map_range

        self.trame_viewer = TrameViewer3D(self.file_list)

    def test_create_drawer_ui_elements_constructs_each_of_the_ui_elements(self):
        self.trame_viewer.disable_2d = mock.MagicMock()
        self.trame_viewer.create_model_selector = mock.MagicMock()
        self.trame_viewer.create_background_selector = mock.MagicMock()
        self.trame_viewer.create_toggle_slice_visibility = mock.MagicMock()
        self.trame_viewer.create_slice_slider = mock.MagicMock()
        self.trame_viewer.create_toggle_window_details_button = mock.MagicMock()
        self.trame_viewer.create_orientation_radio_buttons = mock.MagicMock()
        self.trame_viewer.construct_slice_window_range_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_window_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_level_slider = mock.MagicMock()
        self.trame_viewer.construct_show_slice_histogram_switch = mock.MagicMock()
        self.trame_viewer.create_toggle_volume_visibility = mock.MagicMock()
        self.trame_viewer.create_opacity_radio_buttons = mock.MagicMock()
        self.trame_viewer.create_color_choice_selector = mock.MagicMock()
        self.trame_viewer.create_clipping_toggle = mock.MagicMock()
        self.trame_viewer.create_clipping_removal_button = mock.MagicMock()
        self.trame_viewer.update_windowing_defaults = mock.MagicMock()
        self.trame_viewer.construct_color_slider = mock.MagicMock()
        self.trame_viewer.construct_windowing_slider = mock.MagicMock()
        self.trame_viewer.create_reset_camera_button = mock.MagicMock()
        self.trame_viewer.create_reset_defaults_button = mock.MagicMock()

        self.trame_viewer.create_drawer_ui_elements()

        self.trame_viewer.create_model_selector.assert_called_once_with()
        self.trame_viewer.create_background_selector.assert_called_once_with()
        self.trame_viewer.create_toggle_slice_visibility.assert_called_once_with()
        self.trame_viewer.create_slice_slider.assert_called_once_with(disabled=self.trame_viewer.disable_2d)
        self.trame_viewer.create_toggle_window_details_button.assert_called_once_with(disabled=self.trame_viewer.disable_2d)
        self.trame_viewer.create_orientation_radio_buttons.assert_called_once_with(disabled=self.trame_viewer.disable_2d)
        self.trame_viewer.construct_slice_window_range_slider.assert_called_once_with(disabled=self.trame_viewer.disable_2d)
        self.trame_viewer.construct_slice_window_slider.assert_called_once_with(disabled=self.trame_viewer.disable_2d)
        self.trame_viewer.construct_slice_level_slider.assert_called_once_with(disabled=self.trame_viewer.disable_2d)
        self.trame_viewer.construct_show_slice_histogram_switch.assert_called_once_with(disabled=self.trame_viewer.disable_2d)
        self.trame_viewer.create_toggle_volume_visibility.assert_called_once_with()
        self.trame_viewer.create_opacity_radio_buttons.assert_called_once_with()
        self.trame_viewer.create_color_choice_selector.assert_called_once_with()
        self.trame_viewer.create_clipping_toggle.assert_called_once_with()
        self.trame_viewer.create_clipping_removal_button.assert_called_once_with()
        self.trame_viewer.update_windowing_defaults.assert_called_once_with()
        self.trame_viewer.construct_color_slider.assert_called_once_with()
        self.trame_viewer.construct_windowing_slider.assert_called_once_with()
        self.trame_viewer.create_reset_camera_button.assert_called_once_with()
        self.trame_viewer.create_reset_defaults_button.assert_called_once_with()
        self.assertEqual(self.trame_viewer.background_choice, self.trame_viewer.create_background_selector.return_value)
        self.assertEqual(self.trame_viewer.toggle_slice_visibility, self.trame_viewer.create_toggle_slice_visibility.return_value)
        self.assertEqual(self.trame_viewer.slice_slider, self.trame_viewer.create_slice_slider.return_value)
        self.assertEqual(self.trame_viewer.toggle_window_details_button, self.trame_viewer.create_toggle_window_details_button.return_value)
        self.assertEqual(self.trame_viewer.orientation_radio_buttons, self.trame_viewer.create_orientation_radio_buttons.return_value)
        self.assertEqual(self.trame_viewer.slice_window_range_slider, self.trame_viewer.construct_slice_window_range_slider.return_value)
        self.assertEqual(self.trame_viewer.slice_window_slider, self.trame_viewer.construct_slice_window_slider.return_value)
        self.assertEqual(self.trame_viewer.slice_level_slider, self.trame_viewer.construct_slice_level_slider.return_value)
        self.assertEqual(self.trame_viewer.show_slice_histogram_switch, self.trame_viewer.construct_show_slice_histogram_switch.return_value)
        self.assertEqual(self.trame_viewer.toggle_volume_visibility, self.trame_viewer.create_toggle_volume_visibility.return_value)
        self.assertEqual(self.trame_viewer.opacity_radio_buttons, self.trame_viewer.create_opacity_radio_buttons.return_value)
        self.assertEqual(self.trame_viewer.color_choice, self.trame_viewer.create_color_choice_selector.return_value)
        self.assertEqual(self.trame_viewer.clipping_switch, self.trame_viewer.create_clipping_toggle.return_value)
        self.assertEqual(self.trame_viewer.clipping_removal_button, self.trame_viewer.create_clipping_removal_button.return_value)
        self.assertEqual(self.trame_viewer.color_slider, self.trame_viewer.construct_color_slider.return_value)
        self.assertEqual(self.trame_viewer.windowing_range_slider, self.trame_viewer.construct_windowing_slider.return_value)
        self.assertEqual(self.trame_viewer.reset_cam_button, self.trame_viewer.create_reset_camera_button.return_value)
        self.assertEqual(self.trame_viewer.reset_defaults_button, self.trame_viewer.create_reset_defaults_button.return_value)

    @mock.patch("ccpi.web_viewer.trame_viewer3D.vuetify.VCol")
    @mock.patch("ccpi.web_viewer.trame_viewer3D.vuetify.VRow")
    @mock.patch("ccpi.web_viewer.trame_viewer3D.vuetify.VContainer")
    @mock.patch("ccpi.web_viewer.trame_viewer3D.vuetify.VDivider")
    def test_construct_drawer_layout_sets_layout_children(self, v_divider, v_container, v_row, v_col):
        self.trame_viewer.create_model_selector = mock.MagicMock()
        self.trame_viewer.create_background_selector = mock.MagicMock()
        self.trame_viewer.create_toggle_slice_visibility = mock.MagicMock()
        self.trame_viewer.create_slice_slider = mock.MagicMock()
        self.trame_viewer.create_toggle_window_details_button = mock.MagicMock()
        self.trame_viewer.create_orientation_radio_buttons = mock.MagicMock()
        self.trame_viewer.construct_slice_window_range_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_window_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_level_slider = mock.MagicMock()
        self.trame_viewer.construct_show_slice_histogram_switch = mock.MagicMock()
        self.trame_viewer.create_toggle_volume_visibility = mock.MagicMock()
        self.trame_viewer.create_opacity_radio_buttons = mock.MagicMock()
        self.trame_viewer.create_color_choice_selector = mock.MagicMock()
        self.trame_viewer.create_clipping_toggle = mock.MagicMock()
        self.trame_viewer.create_clipping_removal_button = mock.MagicMock()
        self.trame_viewer.construct_color_slider = mock.MagicMock()
        self.trame_viewer.construct_windowing_slider = mock.MagicMock()
        self.trame_viewer.create_reset_camera_button = mock.MagicMock()
        self.trame_viewer.create_reset_defaults_button = mock.MagicMock()
        self.trame_viewer.update_windowing_defaults = mock.MagicMock()

        self.trame_viewer.create_drawer_ui_elements()
        self.trame_viewer.construct_drawer_layout()

        self.assertEqual(v_col.call_count, 2)
        self.assertIn(call([
            self.trame_viewer.toggle_slice_visibility, self.trame_viewer.slice_slider, self.trame_viewer.orientation_radio_buttons,
            self.trame_viewer.show_slice_histogram_switch, self.trame_viewer.toggle_window_details_button,
            self.trame_viewer.slice_window_range_slider, self.trame_viewer.slice_window_slider, self.trame_viewer.slice_level_slider
        ]), v_col.call_args_list)
        self.assertEqual(self.trame_viewer.slice_interaction_col, v_col.return_value)
        self.assertEqual(self.trame_viewer.slice_interaction_row, v_row.return_value)
        self.assertEqual(self.trame_viewer.slice_interaction_section, v_container.return_value)
        self.assertIn(call([
            self.trame_viewer.toggle_volume_visibility, self.trame_viewer.opacity_radio_buttons, self.trame_viewer.color_choice,
            self.trame_viewer.color_slider, self.trame_viewer.clipping_switch, self.trame_viewer.clipping_removal_button,
            self.trame_viewer.windowing_range_slider
        ]), v_col.call_args_list)
        self.assertEqual(self.trame_viewer.volume_interaction_col, v_col.return_value)
        self.assertEqual(self.trame_viewer.volume_interaction_row, v_row.return_value)
        self.assertEqual(self.trame_viewer.volume_interaction_section, v_container.return_value)
        self.assertEqual(self.trame_viewer.layout.drawer.children,
                         ["Choose model to load", self.trame_viewer.model_choice, v_divider.return_value, "Choose background color",
                          self.trame_viewer.background_choice, v_divider.return_value, self.trame_viewer.slice_interaction_section,
                          v_divider.return_value, self.trame_viewer.volume_interaction_section, v_divider.return_value,
                          self.trame_viewer.reset_cam_button, v_divider.return_value, self.trame_viewer.reset_defaults_button])

    def test_create_reset_defaults_button(self):
        reset_defaults_button = self.trame_viewer.create_reset_defaults_button()

        self.assertIn("Reset defaults", reset_defaults_button.html)
        self.assertEqual(["Reset defaults"], reset_defaults_button.children)
        self.assertEqual(reset_defaults_button._py_attr["click"], self.trame_viewer.reset_defaults)

    def test_construct_show_slice_histogram_switch_not_disabled(self):
        show_slice_histogram_switch = self.trame_viewer.construct_show_slice_histogram_switch(False)

        self.assertIn('label="Show slice histogram"', show_slice_histogram_switch.html)
        self.assertIn('disabled="false"', show_slice_histogram_switch.html)
        self.assertEqual(show_slice_histogram_switch._py_attr["v_model"][0], "show_slice_histogram")
        self.check_vuetify_default(show_slice_histogram_switch, False)

    def test_construct_show_slice_histogram_switch_disabled(self):
        show_slice_histogram_switch = self.trame_viewer.construct_show_slice_histogram_switch(True)

        self.assertIn('label="Show slice histogram"', show_slice_histogram_switch.html)
        self.assertIn('disabled ', show_slice_histogram_switch.html)
        self.assertEqual(show_slice_histogram_switch._py_attr["v_model"][0], "show_slice_histogram")
        self.check_vuetify_default(show_slice_histogram_switch, False)

    def test_create_reset_camera_button(self):
        reset_camera_button = self.trame_viewer.create_reset_camera_button()

        self.assertIn("Reset Camera", reset_camera_button.html)
        self.assertEqual(["Reset Camera"], reset_camera_button.children)
        self.assertEqual(reset_camera_button._py_attr["click"], self.trame_viewer.reset_cam)

    def test_create_clipping_toggle_not_disabled(self):
        self.trame_viewer.disable_3d = False
        clipping_toggle = self.trame_viewer.create_clipping_toggle()

        self.assertIn('label="Toggle Clipping"', clipping_toggle.html)
        self.assertIn('disabled="false"', clipping_toggle.html)
        self.assertEqual(clipping_toggle._py_attr["v_model"][0], "toggle_clipping")
        self.assertEqual(clipping_toggle._py_attr["v_model"][1], False)

    def test_create_clipping_toggle_disabled(self):
        self.trame_viewer.disable_3d = True
        clipping_toggle = self.trame_viewer.create_clipping_toggle()

        self.assertIn('label="Toggle Clipping"', clipping_toggle.html)
        self.assertIn('disabled ', clipping_toggle.html)
        self.assertEqual(clipping_toggle._py_attr["v_model"][0], "toggle_clipping")
        self.check_vuetify_default(clipping_toggle, False)

    def test_create_clipping_removal_button_not_disabled(self):
        self.trame_viewer.disable_3d = False
        clipping_removal_button = self.trame_viewer.create_clipping_removal_button()

        self.assertIn("Remove clipping", clipping_removal_button.html)
        self.assertIn('disabled="false"', clipping_removal_button.html)
        self.assertEqual(["Remove clipping"], clipping_removal_button.children)
        self.assertEqual(clipping_removal_button._py_attr["click"], self.trame_viewer.remove_clipping_plane)

    def test_create_clipping_removal_button_disabled(self):
        self.trame_viewer.disable_3d = True
        clipping_removal_button = self.trame_viewer.create_clipping_removal_button()

        self.assertIn("Remove clipping", clipping_removal_button.html)
        self.assertIn('disabled ', clipping_removal_button.html)
        self.assertEqual(["Remove clipping"], clipping_removal_button.children)
        self.assertEqual(clipping_removal_button._py_attr["click"], self.trame_viewer.remove_clipping_plane)

    def test_create_color_choice_selector_not_disabled(self):
        self.trame_viewer.disable_3d = False
        color_choice_selector = self.trame_viewer.create_color_choice_selector()

        self.assertIn('disabled="false', color_choice_selector.html)
        self.assertEqual(color_choice_selector._py_attr["v_model"][0], "color_map")
        self.check_vuetify_default(color_choice_selector, "viridis")

    def test_create_color_choice_selector_disabled(self):
        self.trame_viewer.disable_3d = True
        color_choice_selector = self.trame_viewer.create_color_choice_selector()

        self.assertIn('disabled ', color_choice_selector.html)
        self.assertEqual(color_choice_selector._py_attr["v_model"][0], "color_map")
        self.check_vuetify_default(color_choice_selector, "viridis")

    def test_create_opacity_radio_buttons_disabled(self):
        opacity_buttons = self.trame_viewer.create_opacity_radio_buttons()
        buttons_checked = 0
        for opacity_button in opacity_buttons.children:
            if 'label="Scalar"' in opacity_button.html:
                self.assertIn('value="scalar"', opacity_button.html)
            elif 'label="Gradient"' in opacity_button.html:
                self.assertIn('value="gradient"', opacity_button.html)
            buttons_checked += 1
        self.assertEqual(buttons_checked, 2)
        self.assertIn('label="Opacity mapping:"', opacity_buttons.html)
        self.check_vuetify_default(opacity_buttons, "scalar")

    def test_create_toggle_volume_visibility(self):
        volume_visibility = self.trame_viewer.create_toggle_volume_visibility()

        self.assertIn('label="3D Volume visibility"', volume_visibility.html)
        self.assertEqual(volume_visibility._py_attr["v_model"][0], "volume_visibility")
        self.check_vuetify_default(volume_visibility, True)

    def test_create_toggle_slice_visibility(self):
        slice_visibility = self.trame_viewer.create_toggle_slice_visibility()

        self.assertIn('label="2D Slice visibility"', slice_visibility.html)
        self.assertEqual(slice_visibility._py_attr["v_model"][0], "slice_visibility")
        self.check_vuetify_default(slice_visibility, True)

    def test_construct_color_slider_uses_percentage_when_cmax_less_than_100(self):
        self.trame_viewer.cmax = 1
        color_slider = self.trame_viewer.construct_color_slider()

        self.assertEqual(self.trame_viewer.color_slider_is_percentage, True)
        self.assertIn('max="100"', color_slider.html)
        self.assertIn('min="0"', color_slider.html)
        self.assertIn('step="0.5"', color_slider.html)
        self.check_vuetify_default(color_slider, self.trame_viewer.windowing_defaults)

    def test_construct_color_slider_does_not_use_percentage_when_cmax_more_than_100(self):
        self.trame_viewer.cmax = 102
        self.trame_viewer.cmin = 0
        color_slider = self.trame_viewer.construct_color_slider()

        self.assertEqual(self.trame_viewer.color_slider_is_percentage, False)
        self.assertIn(f'max="{self.trame_viewer.cmax}"', color_slider.html)
        self.assertIn('min="0"', color_slider.html)
        self.assertIn('step="1"', color_slider.html)
        self.check_vuetify_default(color_slider, self.trame_viewer.windowing_defaults)

    def test_construct_color_slider_disabled(self):
        self.trame_viewer.disable_3d = True
        color_slider = self.trame_viewer.construct_color_slider()

        self.assertIn('disabled ', color_slider.html)

    def test_construct_color_slider_not_disabled(self):
        self.trame_viewer.disable_3d = False
        color_slider = self.trame_viewer.construct_color_slider()

        self.assertIn('disabled="false"', color_slider.html)

    def test_construct_windowing_slider_uses_percentage_when_cmax_less_than_100(self):
        self.trame_viewer.cmax = 1
        windowing_slider = self.trame_viewer.construct_windowing_slider()

        self.assertEqual(self.trame_viewer.windowing_slider_is_percentage, True)
        self.assertIn('max="100"', windowing_slider.html)
        self.assertIn('min="0"', windowing_slider.html)
        self.assertIn('step="0.5"', windowing_slider.html)
        self.check_vuetify_default(windowing_slider, self.trame_viewer.windowing_defaults)

    def test_construct_windowing_slider_does_not_use_percentage_when_cmax_more_than_100(self):
        self.trame_viewer.cmax = 102
        self.trame_viewer.cmin = 0
        windowing_slider = self.trame_viewer.construct_windowing_slider()

        self.assertEqual(self.trame_viewer.windowing_slider_is_percentage, False)
        self.assertIn(f'max="{self.trame_viewer.cmax}"', windowing_slider.html)
        self.assertIn('min="0"', windowing_slider.html)
        self.assertIn('step="1"', windowing_slider.html)
        self.check_vuetify_default(windowing_slider, self.trame_viewer.windowing_defaults)

    def test_construct_windowing_slider_disabled(self):
        self.trame_viewer.disable_3d = True
        windowing_slider = self.trame_viewer.construct_windowing_slider()

        self.assertIn('disabled ', windowing_slider.html)

    def test_construct_windowing_slider_not_disabled(self):
        self.trame_viewer.disable_3d = False
        windowing_slider = self.trame_viewer.construct_windowing_slider()

        self.assertIn('disabled="false"', windowing_slider.html)

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

    def test_update_slice_data(self):
        pass
