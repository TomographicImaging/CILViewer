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

from ccpi.viewer.CILViewerBase import SLICE_ORIENTATION_XY
from ccpi.web_viewer.trame_viewer3D import TrameViewer3D, state


class TrameViewer3DTest(unittest.TestCase):
    # This test has the potential to be flaky on minor version numbers of trame, due to private API usage.
    def check_vuetify_default(self, object_to_check, expected_default):
        self.assertEqual(object_to_check._py_attr["v_model"][1], expected_default)

    @mock.patch("ccpi.web_viewer.trame_viewer3D.CILViewer")
    @mock.patch("ccpi.web_viewer.trame_viewer.vtk")
    @mock.patch("ccpi.web_viewer.trame_viewer3D.TrameViewer3D.update_slice_data")
    def setUp(self, _, vtk_module, cil_viewer):
        # Get the head data
        self.head_path = os.path.join(sys.prefix, 'share', 'cil', 'head.mha')
        self.file_list = [self.head_path, "other_file_path_dir/other_file"]

        # add the cil_viewer and defaults for a default __init__
        self.cil_viewer = cil_viewer
        self.map_range = [0, 3790]
        self.cil_viewer.getImageMapRange.return_value = self.map_range
        self.cil_viewer.img3D.GetExtent().__getitem__ = mock.MagicMock(
            return_value=0)  # Fix issues with errors in the console
        self.cil_viewer.getSliceMapRange.return_value = self.map_range
        self.cil_viewer.getSliceWindowLevelFromRange.return_value = [20, 10]

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
        self.trame_viewer.create_toggle_window_details_button.assert_called_once_with(
            disabled=self.trame_viewer.disable_2d)
        self.trame_viewer.create_orientation_radio_buttons.assert_called_once_with(
            disabled=self.trame_viewer.disable_2d)
        self.trame_viewer.construct_slice_window_range_slider.assert_called_once_with(
            disabled=self.trame_viewer.disable_2d)
        self.trame_viewer.construct_slice_window_slider.assert_called_once_with(disabled=self.trame_viewer.disable_2d)
        self.trame_viewer.construct_slice_level_slider.assert_called_once_with(disabled=self.trame_viewer.disable_2d)
        self.trame_viewer.construct_show_slice_histogram_switch.assert_called_once_with(
            disabled=self.trame_viewer.disable_2d)
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
        self.assertEqual(self.trame_viewer.toggle_slice_visibility,
                         self.trame_viewer.create_toggle_slice_visibility.return_value)
        self.assertEqual(self.trame_viewer.slice_slider, self.trame_viewer.create_slice_slider.return_value)
        self.assertEqual(self.trame_viewer.toggle_window_details_button,
                         self.trame_viewer.create_toggle_window_details_button.return_value)
        self.assertEqual(self.trame_viewer.orientation_radio_buttons,
                         self.trame_viewer.create_orientation_radio_buttons.return_value)
        self.assertEqual(self.trame_viewer.slice_window_range_slider,
                         self.trame_viewer.construct_slice_window_range_slider.return_value)
        self.assertEqual(self.trame_viewer.slice_window_slider,
                         self.trame_viewer.construct_slice_window_slider.return_value)
        self.assertEqual(self.trame_viewer.slice_level_slider,
                         self.trame_viewer.construct_slice_level_slider.return_value)
        self.assertEqual(self.trame_viewer.show_slice_histogram_switch,
                         self.trame_viewer.construct_show_slice_histogram_switch.return_value)
        self.assertEqual(self.trame_viewer.toggle_volume_visibility,
                         self.trame_viewer.create_toggle_volume_visibility.return_value)
        self.assertEqual(self.trame_viewer.opacity_radio_buttons,
                         self.trame_viewer.create_opacity_radio_buttons.return_value)
        self.assertEqual(self.trame_viewer.color_choice, self.trame_viewer.create_color_choice_selector.return_value)
        self.assertEqual(self.trame_viewer.clipping_switch, self.trame_viewer.create_clipping_toggle.return_value)
        self.assertEqual(self.trame_viewer.clipping_removal_button,
                         self.trame_viewer.create_clipping_removal_button.return_value)
        self.assertEqual(self.trame_viewer.color_slider, self.trame_viewer.construct_color_slider.return_value)
        self.assertEqual(self.trame_viewer.windowing_range_slider,
                         self.trame_viewer.construct_windowing_slider.return_value)
        self.assertEqual(self.trame_viewer.reset_cam_button, self.trame_viewer.create_reset_camera_button.return_value)
        self.assertEqual(self.trame_viewer.reset_defaults_button,
                         self.trame_viewer.create_reset_defaults_button.return_value)

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
        self.trame_viewer.create_auto_window_level_button = mock.MagicMock()
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
        self.assertIn(
            call([
                self.trame_viewer.toggle_slice_visibility, self.trame_viewer.slice_slider,
                self.trame_viewer.orientation_radio_buttons, self.trame_viewer.auto_window_level_button,
                self.trame_viewer.show_slice_histogram_switch, self.trame_viewer.toggle_window_details_button,
                self.trame_viewer.slice_window_range_slider, self.trame_viewer.slice_window_slider,
                self.trame_viewer.slice_level_slider
            ]), v_col.call_args_list)
        self.assertEqual(self.trame_viewer.slice_interaction_col, v_col.return_value)
        self.assertEqual(self.trame_viewer.slice_interaction_row, v_row.return_value)
        self.assertEqual(self.trame_viewer.slice_interaction_section, v_container.return_value)
        self.assertIn(
            call([
                self.trame_viewer.toggle_volume_visibility, self.trame_viewer.opacity_radio_buttons,
                self.trame_viewer.color_choice, self.trame_viewer.color_slider, self.trame_viewer.clipping_switch,
                self.trame_viewer.clipping_removal_button, self.trame_viewer.windowing_range_slider
            ]), v_col.call_args_list)
        self.assertEqual(self.trame_viewer.volume_interaction_col, v_col.return_value)
        self.assertEqual(self.trame_viewer.volume_interaction_row, v_row.return_value)
        self.assertEqual(self.trame_viewer.volume_interaction_section, v_container.return_value)
        self.assertEqual(self.trame_viewer.layout.drawer.children, [
            "Choose model to load", self.trame_viewer.model_choice, v_divider.return_value, "Choose background color",
            self.trame_viewer.background_choice, v_divider.return_value, self.trame_viewer.slice_interaction_section,
            v_divider.return_value, self.trame_viewer.volume_interaction_section, v_divider.return_value,
            self.trame_viewer.reset_cam_button, v_divider.return_value, self.trame_viewer.reset_defaults_button
        ])

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

    def test_construct_color_slider_when_sliders_are_percentages(self):
        self.trame_viewer.window_level_sliders_are_percentages = True
        self.trame_viewer.cmax = 1
        color_slider = self.trame_viewer.construct_color_slider()
        self.assertIn('max="100"', color_slider.html)
        self.assertIn('min="0"', color_slider.html)
        self.assertIn('step="0.5"', color_slider.html)
        self.check_vuetify_default(color_slider, self.trame_viewer.windowing_defaults)

    def test_construct_color_slider_when_sliders_are_not_percentages(self):
        self.trame_viewer.window_level_sliders_are_percentages = False
        self.trame_viewer.cmax = 102
        self.trame_viewer.cmin = 0
        color_slider = self.trame_viewer.construct_color_slider()

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

    def test_construct_windowing_slider_when_sliders_are_percentages(self):
        self.trame_viewer.window_level_sliders_are_percentages = True
        self.trame_viewer.cmax = 1
        windowing_slider = self.trame_viewer.construct_windowing_slider()

        self.assertIn('max="100"', windowing_slider.html)
        self.assertIn('min="0"', windowing_slider.html)
        self.assertIn('step="0.5"', windowing_slider.html)
        self.check_vuetify_default(windowing_slider, self.trame_viewer.windowing_defaults)

    def test_construct_windowing_slider_when_sliders_are_not_percentages(self):
        self.trame_viewer.window_level_sliders_are_percentages = False
        self.trame_viewer.cmax = self.map_range[1]
        self.trame_viewer.cmin = self.map_range[0]
        windowing_slider = self.trame_viewer.construct_windowing_slider()

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
        self.trame_viewer.update_slice_data = mock.MagicMock()

        self.trame_viewer.update_windowing_defaults()

        self.trame_viewer.update_slice_data.assert_called_once_with()

    def setup_windowing_defaults_tests(self):
        state["opacity"] = mock.MagicMock()
        self.cil_viewer.getImageMapRange = mock.MagicMock()
        self.trame_viewer.update_slice_data = mock.MagicMock()
        opacity_range = (0., 70.)
        color_range = (0., 100.)
        windowing_defaults = (60, 68)
        coloring_defaults = (5, 95)
        self.cil_viewer.getImageMapRange.side_effect = [
            opacity_range, color_range, windowing_defaults, coloring_defaults
        ]
        self.trame_viewer.construct_windowing_slider = mock.MagicMock()
        self.trame_viewer.construct_color_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_window_range_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_level_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_window_slider = mock.MagicMock()
        self.trame_viewer.disable_2d = mock.MagicMock()
        return opacity_range, color_range, windowing_defaults, coloring_defaults

    def test_update_windowing_defaults_sets_color_and_opacity_ranges(self):
        opacity_range, color_range, _, __ = self.setup_windowing_defaults_tests()
        passed_method = mock.MagicMock()
        self.trame_viewer.update_windowing_defaults(passed_method)
        self.assertEqual(state["opacity"], passed_method)
        self.assertIn(call((0., 100.), passed_method), self.cil_viewer.getImageMapRange.call_args_list)
        self.assertIn(call((0., 100.), "scalar"), self.cil_viewer.getImageMapRange.call_args_list)
        self.assertEqual(self.trame_viewer.cmin, color_range[0])
        self.assertEqual(self.trame_viewer.cmax, color_range[1])
        self.assertEqual(self.trame_viewer.omin, opacity_range[0])
        self.assertEqual(self.trame_viewer.omax, opacity_range[1])

    def test_update_windowing_defaults_sets_values(self):
        opacity_range, color_range, windowing_defaults, coloring_defaults = self.setup_windowing_defaults_tests()
        passed_method = mock.MagicMock()
        self.trame_viewer.update_windowing_defaults(passed_method)
        self.trame_viewer.window_level_sliders_are_percentages = False
        self.assertEqual(self.trame_viewer.coloring_defaults, coloring_defaults)
        self.assertEqual(self.trame_viewer.windowing_defaults, windowing_defaults)
        self.assertIn(call((80., 99.), passed_method), self.cil_viewer.getImageMapRange.call_args_list)
        self.assertIn(call((5., 95.), "scalar"), self.cil_viewer.getImageMapRange.call_args_list)

    def test_update_windowing_defaults_sets_percentages(self):
        self.setup_windowing_defaults_tests()
        passed_method = mock.MagicMock()
        self.trame_viewer.window_level_sliders_are_percentages = True
        self.trame_viewer.update_windowing_defaults(passed_method)
        self.assertEqual(self.trame_viewer.coloring_defaults, (5., 95.))
        self.assertEqual(self.trame_viewer.windowing_defaults, (80., 99.))

    def test_update_windowing_defaults_does_not_update_gui_if_no_window_range_slider(self):
        opacity_range, color_range, windowing_defaults, coloring_defaults = self.setup_windowing_defaults_tests()
        delattr(self.trame_viewer, "windowing_range_slider")

        passed_method = mock.MagicMock()
        self.trame_viewer.update_windowing_defaults(passed_method)
        self.trame_viewer.construct_windowing_slider.assert_not_called()
        self.trame_viewer.construct_color_slider.assert_not_called()
        self.trame_viewer.construct_slice_window_range_slider.assert_not_called()
        self.trame_viewer.construct_slice_level_slider.assert_not_called()
        self.trame_viewer.construct_slice_window_slider.assert_not_called()

    def test_update_windowing_defaults_does_not_update_gui_if_window_present_but_window_range_slider_is_None(self):
        self.setup_windowing_defaults_tests()
        self.trame_viewer.windowing_range_slider = None

        passed_method = mock.MagicMock()
        self.trame_viewer.update_windowing_defaults(passed_method)

        self.trame_viewer.construct_windowing_slider.assert_not_called()
        self.trame_viewer.construct_color_slider.assert_not_called()
        self.trame_viewer.construct_slice_window_range_slider.assert_not_called()
        self.trame_viewer.construct_slice_level_slider.assert_not_called()
        self.trame_viewer.construct_slice_window_slider.assert_not_called()

    def test_update_windowing_defaults_updates_level_window_sliders_if_window_range_slider_present(self):
        self.setup_windowing_defaults_tests()

        passed_method = mock.MagicMock()
        self.trame_viewer.update_windowing_defaults(passed_method)

        self.assertIn(call((0., 100.), passed_method), self.cil_viewer.getImageMapRange.call_args_list)
        self.assertIn(call((80., 99.), passed_method), self.cil_viewer.getImageMapRange.call_args_list)
        self.assertEqual(self.trame_viewer.cmin, 0)
        self.assertEqual(self.trame_viewer.cmax, 100)
        self.trame_viewer.construct_windowing_slider.assert_called_once_with()
        self.trame_viewer.construct_color_slider.assert_called_once_with()
        self.trame_viewer.construct_slice_window_range_slider.assert_called_once_with(self.trame_viewer.disable_2d)
        self.trame_viewer.construct_slice_level_slider.assert_called_once_with(self.trame_viewer.disable_2d)
        self.trame_viewer.construct_slice_window_slider.assert_called_once_with(self.trame_viewer.disable_2d)

    @mock.patch("ccpi.web_viewer.trame_viewer.TrameViewer.load_file")
    def test_load_file_calls_super_class(self, super_load_file):
        file_path = "file/path"

        self.trame_viewer.load_file(file_path)

        super_load_file.assert_called_once_with(file_path, windowing_method="scalar")

    @mock.patch("ccpi.web_viewer.trame_viewer.TrameViewer.load_file")
    def test_load_file_updates_slice_slider_data(self, _):
        self.trame_viewer.update_slice_slider_data = mock.MagicMock()

        self.trame_viewer.load_file("path")

        self.trame_viewer.update_slice_slider_data.assert_called_once_with()

    @mock.patch("ccpi.web_viewer.trame_viewer.TrameViewer.load_file")
    def test_load_file_updates_windowing_defaults(self, _):
        self.trame_viewer.update_windowing_defaults = mock.MagicMock()
        windowing_method = mock.MagicMock()

        self.trame_viewer.load_file("path", windowing_method)

        self.trame_viewer.update_windowing_defaults.assert_called_once_with(windowing_method)


    def test_switch_render_calls_toggle_volume_visibility(self):
        self.cil_viewer.style.ToggleVolumeVisibility = mock.MagicMock()

        self.trame_viewer.switch_render()

        self.cil_viewer.style.ToggleVolumeVisibility.assert_called_once_with()

    def test_switch_slice_toggles_visibility_correctly(self):
        self.cil_viewer.imageSlice = mock.MagicMock()
        self.cil_viewer.imageSlice.GetVisibility = mock.MagicMock(return_value=True)
        self.trame_viewer.switch_slice()
        self.cil_viewer.imageSlice.VisibilityOff.assert_called_once_with()
        self.cil_viewer.imageSlice.VisibilityOn.assert_not_called()

        self.cil_viewer.imageSlice = mock.MagicMock()
        self.cil_viewer.imageSlice.GetVisibility = mock.MagicMock(return_value=False)
        self.trame_viewer.switch_slice()
        self.cil_viewer.imageSlice.VisibilityOn.assert_called_once_with()
        self.cil_viewer.imageSlice.VisibilityOff.assert_not_called()

    def test_change_color_map_passes_cmap_to_setVolumeColorMapName(self):
        cmap = mock.MagicMock()

        self.trame_viewer.change_color_map(cmap)

        self.cil_viewer.setVolumeColorMapName.assert_called_once_with(cmap)

    def test_set_opacity_mapping_sets_volume_render_opacity_method(self):
        opacity = mock.MagicMock()
        self.cil_viewer.setVolumeRenderOpacityMethod = mock.MagicMock()

        self.trame_viewer.set_opacity_mapping(opacity)

        self.cil_viewer.setVolumeRenderOpacityMethod.assert_called_once_with(opacity)

    def test_change_windowing_percentage_and_scalar(self):
        self.cil_viewer.setScalarOpacityPercentiles = mock.MagicMock()
        self.cil_viewer.setGradientOpacityPercentiles = mock.MagicMock()
        self.cil_viewer.setScalarOpacityRange = mock.MagicMock()
        self.cil_viewer.setGradientOpacityRange = mock.MagicMock()
        self.trame_viewer.window_level_sliders_are_percentages = True
        windowing_method = "scalar"
        min_value = mock.MagicMock()
        max_value = mock.MagicMock()

        self.trame_viewer.change_windowing(min_value, max_value, windowing_method)

        self.cil_viewer.setScalarOpacityPercentiles.assert_called_once_with(min_value, max_value)
        self.cil_viewer.setGradientOpacityPercentiles.assert_not_called()
        self.cil_viewer.setScalarOpacityRange.assert_not_called()
        self.cil_viewer.setGradientOpacityRange.assert_not_called()

    def test_change_windowing_percentage_and_gradient(self):
        self.cil_viewer.setScalarOpacityPercentiles = mock.MagicMock()
        self.cil_viewer.setGradientOpacityPercentiles = mock.MagicMock()
        self.cil_viewer.setScalarOpacityRange = mock.MagicMock()
        self.cil_viewer.setGradientOpacityRange = mock.MagicMock()
        self.trame_viewer.window_level_sliders_are_percentages = True
        windowing_method = "gradient"
        min_value = mock.MagicMock()
        max_value = mock.MagicMock()

        self.trame_viewer.change_windowing(min_value, max_value, windowing_method)

        self.cil_viewer.setScalarOpacityPercentiles.assert_not_called()
        self.cil_viewer.setGradientOpacityPercentiles.assert_called_once_with(min_value, max_value)
        self.cil_viewer.setScalarOpacityRange.assert_not_called()
        self.cil_viewer.setGradientOpacityRange.assert_not_called()

    def test_change_windowing_not_percentage_and_scalar(self):
        self.cil_viewer.setScalarOpacityPercentiles = mock.MagicMock()
        self.cil_viewer.setGradientOpacityPercentiles = mock.MagicMock()
        self.cil_viewer.setScalarOpacityRange = mock.MagicMock()
        self.cil_viewer.setGradientOpacityRange = mock.MagicMock()
        self.trame_viewer.window_level_sliders_are_percentages = False
        windowing_method = "scalar"
        min_value = mock.MagicMock()
        max_value = mock.MagicMock()

        self.trame_viewer.change_windowing(min_value, max_value, windowing_method)

        self.cil_viewer.setScalarOpacityPercentiles.assert_not_called()
        self.cil_viewer.setGradientOpacityPercentiles.assert_not_called()
        self.cil_viewer.setScalarOpacityRange.assert_called_once_with(min_value, max_value)
        self.cil_viewer.setGradientOpacityRange.assert_not_called()

    def test_change_windowing_not_percentage_and_gradient(self):
        self.cil_viewer.setScalarOpacityPercentiles = mock.MagicMock()
        self.cil_viewer.setGradientOpacityPercentiles = mock.MagicMock()
        self.cil_viewer.setScalarOpacityRange = mock.MagicMock()
        self.cil_viewer.setGradientOpacityRange = mock.MagicMock()
        self.trame_viewer.window_level_sliders_are_percentages = False
        windowing_method = "gradient"
        min_value = mock.MagicMock()
        max_value = mock.MagicMock()

        self.trame_viewer.change_windowing(min_value, max_value, windowing_method)

        self.cil_viewer.setScalarOpacityPercentiles.assert_not_called()
        self.cil_viewer.setGradientOpacityPercentiles.assert_not_called()
        self.cil_viewer.setScalarOpacityRange.assert_not_called()
        self.cil_viewer.setGradientOpacityRange.assert_called_once_with(min_value, max_value)

    def test_reset_cam_only_calls_reset_camera_to_default_without_html_view(self):
        self.trame_viewer.cil_viewer = mock.MagicMock()
        self.trame_viewer.html_view = mock.MagicMock()
        delattr(self.trame_viewer, "html_view")

        self.trame_viewer.reset_cam()

        self.cil_viewer.resetCameraToDefault.assert_called_once()
        self.assertFalse(hasattr(self.trame_viewer, "html_view"))


    def test_reset_cam_updates_html_view_if_html_view_is_set(self):
        self.trame_viewer.cil_viewer = mock.MagicMock()
        self.trame_viewer.html_view = mock.MagicMock()

        self.trame_viewer.reset_cam()

        self.cil_viewer.resetCameraToDefault.assert_called_once()
        self.trame_viewer.html_view.update.assert_called_once_with()

    def test_reset_defaults(self):
        self.trame_viewer.set_default_button_state = mock.MagicMock()
        self.trame_viewer.reset_cam = mock.MagicMock()

        self.trame_viewer.reset_defaults()

        self.trame_viewer.set_default_button_state.assert_called_once_with()
        self.trame_viewer.reset_cam.assert_called_once_with()

    def setup_default_button_state_tests(self):
        state["slice"] = mock.MagicMock()
        state["orientation"] = mock.MagicMock()
        state["opacity"] = mock.MagicMock()
        state["color_map"] = mock.MagicMock()
        state["windowing"] = mock.MagicMock()
        state["coloring"] = mock.MagicMock()
        state["slice_visibility"] = mock.MagicMock()
        state["volume_visibility"] = mock.MagicMock()
        state["slice_detailed_sliders"] = mock.MagicMock()
        state["slice_window_range"] = mock.MagicMock()
        state["slice_window"] = mock.MagicMock()
        state["slice_level"] = mock.MagicMock()
        state["background_color"] = mock.MagicMock()
        state["toggle_clipping"] = mock.MagicMock()
        state["show_slice_histogram"] = mock.MagicMock()

        state["slice_window_range"] = mock.MagicMock()
        state["slice_window"] = mock.MagicMock()
        state["slice_level"] = mock.MagicMock()

        state["slice_window_percentiles"] = mock.MagicMock()
        state["slice_window_as_percentage"] = mock.MagicMock()
        state["slice_level_as_percentage"] = mock.MagicMock()

    def test_set_default_button_state_sets_correct_defaults(self):
        self.setup_default_button_state_tests()
        self.trame_viewer.set_default_button_state()

        self.assertEqual(state["slice"], self.trame_viewer.default_slice)
        self.assertEqual(state["orientation"], f"{SLICE_ORIENTATION_XY}")
        self.assertEqual(state["opacity"], "scalar")
        self.assertEqual(state["color_map"], "viridis")
        self.assertEqual(state["windowing"], self.trame_viewer.windowing_defaults)
        self.assertEqual(state["coloring"], self.trame_viewer.coloring_defaults)
        self.assertEqual(state["slice_visibility"], True)
        self.assertEqual(state["volume_visibility"], True)
        self.assertEqual(state["slice_detailed_sliders"], False)
        self.assertEqual(state["background_color"], "cil_viewer_blue")
        self.assertEqual(state["toggle_clipping"], False)
        self.assertEqual(state["show_slice_histogram"], False)

    def test_set_default_button_state_sets_correct_defaults_for_slice_windowing_if_not_using_percentages(self):
        self.setup_default_button_state_tests()
        self.trame_viewer.window_level_sliders_are_percentages = False
        self.trame_viewer.set_default_button_state()

        window_range = self.cil_viewer.getImageMapRange((5., 95.), "scalar")
        window = self.cil_viewer.getSliceWindowLevelFromRange(window_range)[0]
        level = self.cil_viewer.getSliceWindowLevelFromRange(window_range)[1]

        self.assertEqual(state["slice_window_range"], tuple(window_range))
        self.assertEqual(state["slice_window"], window)
        self.assertEqual(state["slice_level"], level)

    def test_set_default_button_state_sets_correct_defaults_for_slice_windowing_if_using_percentages(self):

        self.setup_default_button_state_tests()
        self.trame_viewer.window_level_sliders_are_percentages = True
        self.trame_viewer.set_default_button_state()

        window_range = self.cil_viewer.getImageMapRange((5., 95.), "scalar")
        window = self.cil_viewer.getSliceWindowLevelFromRange(window_range)[0]
        level = self.cil_viewer.getSliceWindowLevelFromRange(window_range)[1]

        self.assertEqual(state["slice_window_percentiles"], (5., 95.))
        self.assertEqual(state["slice_window_as_percentage"], self.trame_viewer.convert_value_to_percentage(window))
        self.assertEqual(state["slice_level_as_percentage"], self.trame_viewer.convert_value_to_percentage(level))

    def test_set_default_button_state_sets_visibility_of_the_slice(self):
        self.trame_viewer.switch_slice = mock.MagicMock()
        self.cil_viewer.imageSlice.GetVisibility = mock.MagicMock(return_value=True)

        self.trame_viewer.set_default_button_state()

        self.trame_viewer.switch_slice.assert_not_called()

        self.cil_viewer.imageSlice.GetVisibility = mock.MagicMock(return_value=False)

        self.trame_viewer.set_default_button_state()

        self.trame_viewer.switch_slice.assert_called_once_with()

    def test_set_default_button_state_sets_visibility_of_the_volume(self):
        self.trame_viewer.switch_render = mock.MagicMock()
        self.cil_viewer.volume.GetVisibility = mock.MagicMock(return_value=True)

        self.trame_viewer.set_default_button_state()

        self.trame_viewer.switch_render.assert_not_called()

        self.cil_viewer.volume.GetVisibility = mock.MagicMock(return_value=False)

        self.trame_viewer.set_default_button_state()

        self.trame_viewer.switch_render.assert_called_once_with()

    def test_set_default_button_state_removes_clipping_planes_if_present(self):
        self.cil_viewer.volume.GetMapper.return_value.RemoveAllClippingPlanes = mock.MagicMock()
        self.cil_viewer.volume.GetMapper.return_value.GetClippingPlanes.return_value = None

        self.trame_viewer.set_default_button_state()

        self.cil_viewer.volume.GetMapper.return_value.RemoveAllClippingPlanes.assert_not_called()

        self.cil_viewer.volume.GetMapper.return_value.GetClippingPlanes.return_value = mock.MagicMock()

        self.trame_viewer.set_default_button_state()

        self.cil_viewer.volume.GetMapper.return_value.RemoveAllClippingPlanes.assert_called_once_with()

    def test_set_default_button_state_removes_clipping_planes_if_clipping_plane_initialised_is_True(self):
        self.cil_viewer.clipping_plane_initialised = False
        self.trame_viewer.remove_clipping_plane = mock.MagicMock()
        self.cil_viewer.style.SetVolumeClipping = mock.MagicMock()

        self.trame_viewer.set_default_button_state()

        self.cil_viewer.style.SetVolumeClipping.assert_not_called()
        self.trame_viewer.remove_clipping_plane.assert_not_called()

        self.cil_viewer.clipping_plane_initialised = True

        self.trame_viewer.set_default_button_state()

        self.cil_viewer.style.SetVolumeClipping.assert_called_once_with(False)
        self.trame_viewer.remove_clipping_plane.assert_called_once_with()

    def test_change_coloring_percentage(self):
        self.trame_viewer.window_level_sliders_are_percentages = True
        min_value = mock.MagicMock()
        max_value = mock.MagicMock()

        self.trame_viewer.change_coloring(min_value, max_value)

        self.cil_viewer.setVolumeColorPercentiles.assert_called_once_with(min_value, max_value)
        self.cil_viewer.setVolumeColorRange.assert_not_called()

    def test_change_coloring_not_percentage(self):
        self.trame_viewer.window_level_sliders_are_percentages = False
        min_value = mock.MagicMock()
        max_value = mock.MagicMock()

        self.trame_viewer.change_coloring(min_value, max_value)

        self.cil_viewer.setVolumeColorPercentiles.assert_not_called()
        self.cil_viewer.setVolumeColorRange.assert_called_once_with(min_value, max_value)

    @mock.patch("ccpi.web_viewer.trame_viewer.TrameViewer.change_window_level_detail_sliders")
    def test_change_window_level_detail_sliders_calls_super(self, change_window_level_detail_sliders):
        show_detailed = mock.MagicMock()

        self.trame_viewer.change_window_level_detail_sliders(show_detailed)

        change_window_level_detail_sliders.assert_called_once_with(show_detailed)

    @mock.patch("ccpi.web_viewer.trame_viewer.TrameViewer.change_window_level_detail_sliders")
    def test_change_window_level_detail_sliders_recreates_sliders_and_pushes(self, _):
        show_detailed = mock.MagicMock()
        disable_2d = mock.MagicMock()
        self.trame_viewer.disable_2d = disable_2d
        self.trame_viewer.construct_slice_window_range_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_window_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_level_slider = mock.MagicMock()
        self.trame_viewer.construct_drawer_layout = mock.MagicMock()

        self.trame_viewer.change_window_level_detail_sliders(show_detailed)

        self.trame_viewer.construct_slice_window_range_slider.assert_called_once_with(disable_2d)
        self.trame_viewer.construct_slice_window_slider.assert_called_once_with(disable_2d)
        self.trame_viewer.construct_slice_level_slider.assert_called_once_with(disable_2d)
        self.trame_viewer.construct_drawer_layout.assert_called_once_with()

    def test_change_slice_visibility_if_visibility_true(self):
        visibility = True

        self.trame_viewer.change_slice_visibility(visibility)

        self.assertEqual(False, self.trame_viewer.disable_2d)
        self.cil_viewer.imageSlice.VisibilityOn.assert_called_once_with()
        self.cil_viewer.imageSlice.VisibilityOff.assert_not_called()

    def test_change_slice_visibility_if_visibility_false(self):
        visibility = False

        self.trame_viewer.change_slice_visibility(visibility)

        self.assertEqual(True, self.trame_viewer.disable_2d)
        self.assertEqual(state["show_slice_histogram"], False)
        self.cil_viewer.imageSlice.VisibilityOff.assert_called_once_with()
        self.cil_viewer.imageSlice.VisibilityOn.assert_not_called()

    def test_change_slice_visibility_redraws_ui_and_pushes(self):
        self.trame_viewer.create_drawer_ui_elements = mock.MagicMock()
        self.trame_viewer.layout.flush_content = mock.MagicMock()
        self.trame_viewer.cil_viewer.updatePipeline = mock.MagicMock()

        self.trame_viewer.change_slice_visibility(False)

        self.trame_viewer.create_drawer_ui_elements.assert_called_once_with()
        self.trame_viewer.layout.flush_content.assert_called_once_with()
        self.trame_viewer.cil_viewer.updatePipeline.assert_called_once_with()

    def test_change_volume_visibility_volume_render_toggle(self):
        self.cil_viewer.installVolumeRenderActorPipeline = mock.MagicMock()
        self.cil_viewer.volume_render_initialised = True

        self.trame_viewer.change_volume_visibility(True)

        self.cil_viewer.installVolumeRenderActorPipeline.assert_not_called()

        self.cil_viewer.volume_render_initialised = False

        self.trame_viewer.change_volume_visibility(True)

        self.cil_viewer.installVolumeRenderActorPipeline.assert_called_once_with()

    def test_change_volume_visibility_if_visibility_true(self):
        visibility = True

        self.trame_viewer.change_volume_visibility(visibility)

        self.assertEqual(False, self.trame_viewer.disable_3d)
        self.cil_viewer.style.SetVolumeVisibility.assert_called_once_with(visibility)

    def test_change_volume_visibility_if_visibility_false(self):
        visibility = False

        self.trame_viewer.change_volume_visibility(visibility)

        self.assertEqual(True, self.trame_viewer.disable_3d)
        self.cil_viewer.style.SetVolumeVisibility.assert_called_once_with(visibility)

    def test_change_volume_visibility_sets_volume_visible_to_passed_value(self):
        visibility = mock.MagicMock()

        self.trame_viewer.change_volume_visibility(visibility)

        self.cil_viewer.style.SetVolumeVisibility.assert_called_once_with(visibility)

    def test_change_volume_visibility_redraws_ui_and_flush_to_client(self):
        self.trame_viewer.create_drawer_ui_elements = mock.MagicMock()
        self.trame_viewer.layout.flush_content = mock.MagicMock()
        self.trame_viewer.cil_viewer.updatePipeline = mock.MagicMock()

        self.trame_viewer.change_volume_visibility(False)

        self.trame_viewer.create_drawer_ui_elements.assert_called_once_with()
        self.trame_viewer.layout.flush_content.assert_called_once_with()
        self.trame_viewer.cil_viewer.updatePipeline.assert_called_once_with()

    def test_change_clipping_false(self):
        slice_visibility_val = mock.MagicMock()
        state["slice_visibility"] = slice_visibility_val
        self.cil_viewer.style.SetVolumeClipping = mock.MagicMock()

        self.trame_viewer.change_clipping(False)

        self.assertEqual(slice_visibility_val, state["slice_visibility"])
        self.cil_viewer.style.SetVolumeClipping.assert_called_once_with(False)

    def test_change_clipping_true(self):
        slice_visibility_val = mock.MagicMock()
        state["slice_visibility"] = slice_visibility_val
        self.cil_viewer.style.SetVolumeClipping = mock.MagicMock()

        self.trame_viewer.change_clipping(True)

        self.assertEqual(False, state["slice_visibility"])
        self.cil_viewer.style.SetVolumeClipping.assert_called_once_with(True)

    def test_remove_clipping_plane_where_planew_is_not_set_does_nothing(self):
        self.cil_viewer.remove_clipping_plane = mock.MagicMock()
        self.cil_viewer.getRenderer = mock.MagicMock()
        self.cil_viewer.updatePipeline = mock.MagicMock()
        clipping = mock.MagicMock()
        state["toggle_clipping"] = clipping
        delattr(self.trame_viewer.cil_viewer, "planew")

        self.trame_viewer.remove_clipping_plane()

        self.assertEqual(state["toggle_clipping"], clipping)
        self.cil_viewer.remove_clipping_plane.assert_not_called()
        self.cil_viewer.getRenderer.assert_not_called()
        self.cil_viewer.updatePipeline.assert_not_called()

    def test_remove_clipping_plane_where_planew_is_set(self):
        self.cil_viewer.remove_clipping_plane = mock.MagicMock()
        self.cil_viewer.getRenderer = mock.MagicMock()
        self.cil_viewer.updatePipeline = mock.MagicMock()
        clipping = mock.MagicMock()
        state["toggle_clipping"] = clipping
        self.trame_viewer.cil_viewer.planew = mock.MagicMock()

        self.trame_viewer.remove_clipping_plane()

        self.assertEqual(state["toggle_clipping"], False)
        self.cil_viewer.remove_clipping_plane.assert_called_once_with()
        self.cil_viewer.getRenderer.assert_called_once_with()
        self.cil_viewer.getRenderer.return_value.Render.assert_called_once_with()
        self.cil_viewer.updatePipeline.assert_called_once_with()

    def test_show_slice_histogram_where_show_histogram_is_true(self):
        self.cil_viewer.updateSliceHistogram = mock.MagicMock()
        show_histogram = True

        self.trame_viewer.show_slice_histogram(show_histogram)

        self.cil_viewer.updateSliceHistogram.assert_called_once_with()
        self.cil_viewer.histogramPlotActor.VisibilityOn.assert_called_once_with()
        self.cil_viewer.histogramPlotActor.VisibilityOff.assert_not_called()

    def test_show_slice_histogram_where_show_histogram_is_false(self):
        self.cil_viewer.updateSliceHistogram = mock.MagicMock()
        show_histogram = False

        self.trame_viewer.show_slice_histogram(show_histogram)

        self.cil_viewer.updateSliceHistogram.assert_called_once_with()
        self.cil_viewer.histogramPlotActor.VisibilityOff.assert_called_once_with()
        self.cil_viewer.histogramPlotActor.VisibilityOn.assert_not_called()

    def test_change_slice_number(self):
        self.trame_viewer.cil_viewer = mock.MagicMock()
        self.trame_viewer.html_view = mock.MagicMock()
        slice_number = mock.MagicMock()

        self.trame_viewer.change_slice_number(slice_number)

        self.trame_viewer.cil_viewer.updateSliceHistogram.assert_called_once_with()
        self.trame_viewer.cil_viewer.setActiveSlice.assert_called_once_with(slice_number)
        self.trame_viewer.cil_viewer.updatePipeline.assert_called_once_with()
        self.trame_viewer.html_view.update.assert_called_once_with()
