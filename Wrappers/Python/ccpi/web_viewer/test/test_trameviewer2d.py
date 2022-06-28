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
import random
from unittest import mock
from unittest.mock import call

from ccpi.viewer.CILViewerBase import SLICE_ORIENTATION_XY
from ccpi.web_viewer.trame_viewer2D import TrameViewer2D, state


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
        self.trame_viewer.create_model_selector = mock.MagicMock()
        self.trame_viewer.create_background_selector = mock.MagicMock()
        self.trame_viewer.create_slice_slider = mock.MagicMock()
        self.trame_viewer.create_orientation_radio_buttons = mock.MagicMock()
        self.trame_viewer.create_toggle_window_details_button = mock.MagicMock()
        self.trame_viewer.create_auto_window_level_button = mock.MagicMock()
        self.trame_viewer.construct_slice_window_range_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_window_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_level_slider = mock.MagicMock()
        self.trame_viewer.create_tracing_switch = mock.MagicMock()
        self.trame_viewer.create_interpolation_of_slice_switch = mock.MagicMock()
        self.trame_viewer.create_remove_roi_button = mock.MagicMock()
        self.trame_viewer.create_reset_defaults_button = mock.MagicMock()

        self.trame_viewer.create_drawer_ui_elements()

        self.trame_viewer.create_model_selector.assert_called_once()
        self.trame_viewer.create_background_selector.assert_called_once()
        self.trame_viewer.create_slice_slider.assert_called_once()
        self.trame_viewer.create_orientation_radio_buttons.assert_called_once()
        self.trame_viewer.create_toggle_window_details_button.assert_called_once()
        self.trame_viewer.create_auto_window_level_button.assert_called_once()
        self.trame_viewer.construct_slice_window_range_slider.assert_called_once()
        self.trame_viewer.construct_slice_window_slider.assert_called_once()
        self.trame_viewer.construct_slice_level_slider.assert_called_once()
        self.trame_viewer.create_tracing_switch.assert_called_once()
        self.trame_viewer.create_interpolation_of_slice_switch.assert_called_once()
        self.trame_viewer.create_remove_roi_button.assert_called_once()
        self.trame_viewer.create_reset_defaults_button.assert_called_once()

    @mock.patch("ccpi.web_viewer.trame_viewer2D.vuetify.VCol")
    @mock.patch("ccpi.web_viewer.trame_viewer2D.vuetify.VRow")
    @mock.patch("ccpi.web_viewer.trame_viewer2D.vuetify.VContainer")
    @mock.patch("ccpi.web_viewer.trame_viewer2D.vuetify.VDivider")
    def test_construct_drawer_layout_sets_layout_children(self, v_divider, v_container, v_row, v_col):
        self.trame_viewer.create_model_selector = mock.MagicMock()
        self.trame_viewer.create_background_selector = mock.MagicMock()
        self.trame_viewer.create_slice_slider = mock.MagicMock()
        self.trame_viewer.create_orientation_radio_buttons = mock.MagicMock()
        self.trame_viewer.create_toggle_window_details_button = mock.MagicMock()
        self.trame_viewer.create_auto_window_level_button = mock.MagicMock()
        self.trame_viewer.construct_slice_window_range_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_window_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_level_slider = mock.MagicMock()
        self.trame_viewer.create_tracing_switch = mock.MagicMock()
        self.trame_viewer.create_interpolation_of_slice_switch = mock.MagicMock()
        self.trame_viewer.create_remove_roi_button = mock.MagicMock()
        self.trame_viewer.create_reset_defaults_button = mock.MagicMock()

        self.trame_viewer.create_drawer_ui_elements()
        self.trame_viewer.construct_drawer_layout()

        v_col.assert_called_once_with([
            self.trame_viewer.slice_slider, self.trame_viewer.orientation_radio_buttons,
            self.trame_viewer.auto_window_level_button, self.trame_viewer.toggle_window_details_button,
            self.trame_viewer.slice_window_range_slider, self.trame_viewer.slice_window_slider,
            self.trame_viewer.slice_level_slider, self.trame_viewer.tracing_switch,
            self.trame_viewer.interpolation_of_slice_switch
        ])
        self.assertEqual(self.trame_viewer.slice_interaction_col, v_col.return_value)
        self.assertEqual(self.trame_viewer.slice_interaction_row, v_row.return_value)
        self.assertEqual(self.trame_viewer.slice_interaction_section, v_container.return_value)
        self.assertEqual(self.trame_viewer.layout.drawer.children, [
            "Choose model to load", self.trame_viewer.model_choice, v_divider.return_value, "Choose background color",
            self.trame_viewer.background_choice, v_divider.return_value, self.trame_viewer.slice_interaction_section,
            v_divider.return_value,
            "Use Ctrl + Click on the slice, to show the ROI of the current slice, Click and drag to resize and reposition.\n"
            "Move the ROI by using the middle mouse button.", v_divider.return_value,
            self.trame_viewer.remove_roi_button, v_divider.return_value, self.trame_viewer.reset_defaults_button
        ])

    @mock.patch("ccpi.web_viewer.trame_viewer.TrameViewer.load_file")
    def test_load_file_calls_super_class(self, super_load_file):
        file_path = "file/path"

        self.trame_viewer.load_file(file_path)

        super_load_file.assert_called_once_with(file_path, windowing_method="scalar")

    def test_load_file_if_not_first_load(self):
        file_path = "file/path"
        self.trame_viewer.first_load = False
        self.trame_viewer.update_slice_slider_data = mock.MagicMock()
        self.trame_viewer.update_slice_windowing_defaults = mock.MagicMock()
        self.trame_viewer.create_drawer_ui_elements = mock.MagicMock()
        self.trame_viewer.construct_drawer_layout = mock.MagicMock()
        self.trame_viewer.reset_defaults = mock.MagicMock()

        self.trame_viewer.load_file(file_path)

        self.trame_viewer.update_slice_slider_data.assert_called_once_with()
        self.trame_viewer.update_slice_windowing_defaults.assert_called_once_with()
        self.trame_viewer.create_drawer_ui_elements.assert_called_once_with()
        self.trame_viewer.construct_drawer_layout.assert_called_once_with()
        self.trame_viewer.reset_defaults.assert_called_once_with()

    def test_load_file_if_first_load(self):
        file_path = "file/path"
        self.trame_viewer.first_load = True
        self.trame_viewer.update_slice_slider_data = mock.MagicMock()
        self.trame_viewer.update_slice_windowing_defaults = mock.MagicMock()
        self.trame_viewer.create_drawer_ui_elements = mock.MagicMock()
        self.trame_viewer.construct_drawer_layout = mock.MagicMock()
        self.trame_viewer.reset_defaults = mock.MagicMock()

        self.trame_viewer.load_file(file_path)

        self.assertEqual(self.trame_viewer.first_load, False)
        self.trame_viewer.update_slice_slider_data.assert_not_called()
        self.trame_viewer.update_slice_windowing_defaults.assert_not_called()
        self.trame_viewer.create_drawer_ui_elements.assert_not_called()
        self.trame_viewer.construct_drawer_layout.assert_not_called()
        self.trame_viewer.reset_defaults.assert_not_called()

    def test_update_slice_windowing_defaults_calls_update_slice_data(self):
        self.trame_viewer.update_slice_data = mock.MagicMock()

        self.trame_viewer.update_slice_windowing_defaults()

        self.trame_viewer.update_slice_data.assert_called_once_with()

    def test_update_slice_windowing_defaults_does_not_update_slice_data_if_no_slice_window_range_slider(self):
        self.trame_viewer.update_slice_data = mock.MagicMock()
        self.trame_viewer.construct_slice_window_range_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_level_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_window_slider = mock.MagicMock()
        delattr(self.trame_viewer, "slice_window_range_slider")

        self.trame_viewer.update_slice_windowing_defaults()

        self.trame_viewer.construct_slice_window_range_slider.assert_not_called()
        self.trame_viewer.construct_slice_level_slider.assert_not_called()
        self.trame_viewer.construct_slice_window_slider.assert_not_called()

    def test_update_slice_windowing_defaults_does_not_update_slice_data_if_slide_window_present_but_slice_window_range_slider_is_false(
            self):
        self.trame_viewer.update_slice_data = mock.MagicMock()
        self.trame_viewer.slice_window_range_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_window_range_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_level_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_window_slider = mock.MagicMock()
        self.trame_viewer.slice_window_range_slider = False

        self.trame_viewer.update_slice_windowing_defaults()

        self.trame_viewer.construct_slice_window_range_slider.assert_not_called()
        self.trame_viewer.construct_slice_level_slider.assert_not_called()
        self.trame_viewer.construct_slice_window_slider.assert_not_called()

    def test_update_slice_windowing_defaults_updates_level_window_sliders_if_slice_window_range_slider_present(self):
        self.trame_viewer.update_slice_data = mock.MagicMock()
        self.trame_viewer.slice_window_range_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_window_range_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_level_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_window_slider = mock.MagicMock()
        self.trame_viewer.slice_window_range_slider = True

        self.trame_viewer.update_slice_windowing_defaults()

        self.trame_viewer.construct_slice_window_range_slider.assert_called_once_with()
        self.trame_viewer.construct_slice_level_slider.assert_called_once_with()
        self.trame_viewer.construct_slice_window_slider.assert_called_once_with()

    def test_create_remove_roi_button(self):
        roi_button = self.trame_viewer.create_remove_roi_button()

        self.assertIn("Remove ROI", roi_button.html)
        self.assertEqual(["Remove ROI"], roi_button.children)
        self.assertEqual(roi_button._py_attr["click"], self.trame_viewer.remove_roi)

    def test_create_auto_window_level_button(self):
        auto_window_level_button = self.trame_viewer.create_auto_window_level_button()

        self.assertIn("Auto Window/Level", auto_window_level_button.html)
        self.assertEqual(["Auto Window/Level"], auto_window_level_button.children)
        self.assertEqual(auto_window_level_button._py_attr["click"], self.trame_viewer.auto_window_level)

    def test_create_tracing_switch(self):
        tracing_switch = self.trame_viewer.create_tracing_switch()

        self.assertIn('label="Toggle Tracing"', tracing_switch.html)
        self.assertEqual(tracing_switch._py_attr["v_model"][0], "toggle_tracing")
        self.assertEqual(tracing_switch._py_attr["v_model"][1], False)

    def test_create_interpolation_of_slice_switch(self):
        interpolation_of_slice_switch = self.trame_viewer.create_interpolation_of_slice_switch()

        self.assertIn('label="Toggle Interpolation"', interpolation_of_slice_switch.html)
        self.assertEqual(interpolation_of_slice_switch._py_attr["v_model"][0], "toggle_interpolation")
        self.assertEqual(interpolation_of_slice_switch._py_attr["v_model"][1], False)

    def test_create_reset_defaults_button(self):
        reset_defaults_button = self.trame_viewer.create_reset_defaults_button()

        self.assertIn("Reset Defaults", reset_defaults_button.html)
        self.assertEqual(["Reset Defaults"], reset_defaults_button.children)
        self.assertEqual(reset_defaults_button._py_attr["click"], self.trame_viewer.reset_defaults)

    def test_change_tracing_turns_tracing_on_when_passed_true(self):
        self.trame_viewer.cil_viewer.imageTracer = mock.MagicMock()

        self.trame_viewer.change_tracing(True)

        self.trame_viewer.cil_viewer.imageTracer.On.assert_called_once()
        self.trame_viewer.cil_viewer.imageTracer.Off.assert_not_called()

    def test_change_tracing_turn_tracing_off_when_passed_false(self):
        self.trame_viewer.cil_viewer.imageTracer = mock.MagicMock()

        self.trame_viewer.change_tracing(False)

        self.trame_viewer.cil_viewer.imageTracer.Off.assert_called_once()
        self.trame_viewer.cil_viewer.imageTracer.On.assert_not_called()

    def test_change_interpolation_sets_linear_when_passed_true(self):
        self.trame_viewer.cil_viewer.imageSlice.GetProperty = mock.MagicMock()

        self.trame_viewer.change_interpolation(True)

        self.trame_viewer.cil_viewer.imageSlice.GetProperty.return_value.SetInterpolationTypeToNearest.assert_not_called(
        )
        self.trame_viewer.cil_viewer.imageSlice.GetProperty.return_value.SetInterpolationTypeToLinear.assert_called_once_with(
        )

    def test_change_interpolation_sets_nearest_when_interpolation_false(self):
        self.trame_viewer.cil_viewer.imageSlice.GetProperty = mock.MagicMock()

        self.trame_viewer.change_interpolation(False)

        self.trame_viewer.cil_viewer.imageSlice.GetProperty.return_value.SetInterpolationTypeToLinear.assert_not_called(
        )
        self.trame_viewer.cil_viewer.imageSlice.GetProperty.return_value.SetInterpolationTypeToNearest.assert_called_once_with(
        )

    def test_auto_window_level_calculates_window_level_correctly(self):
        self.trame_viewer.cil_viewer.ia.GetAutoRange.return_value = [0, 3700]

        self.trame_viewer.auto_window_level()

        self.assertEqual(state["slice_window_range"], (3700, 1850.))
        self.assertEqual(state["slice_window"], 3700)
        self.assertEqual(state["slice_level"], 1850.)

    @mock.patch("ccpi.web_viewer.trame_viewer.TrameViewer.change_window_level_detail_sliders")
    def test_change_window_level_detail_sliders_calls_super_with_what_is_passed(self, super_method):
        show_detailed_passed = mock.MagicMock()

        self.trame_viewer.change_window_level_detail_sliders(show_detailed_passed)

        super_method.assert_called_once_with(show_detailed_passed)

    def test_change_window_level_detail_sliders_constructs_slice_window_level_and_updates_the_drawer(self):
        self.trame_viewer.construct_slice_window_range_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_window_slider = mock.MagicMock()
        self.trame_viewer.construct_slice_level_slider = mock.MagicMock()
        self.trame_viewer.construct_drawer_layout = mock.MagicMock()

        self.trame_viewer.change_window_level_detail_sliders(False)

        self.assertEqual(self.trame_viewer.slice_window_range_slider,
                         self.trame_viewer.construct_slice_window_range_slider.return_value)
        self.assertEqual(self.trame_viewer.slice_window_slider,
                         self.trame_viewer.construct_slice_window_slider.return_value)
        self.assertEqual(self.trame_viewer.slice_level_slider,
                         self.trame_viewer.construct_slice_level_slider.return_value)
        self.trame_viewer.construct_drawer_layout.assert_called_once_with()

    def test_remove_roi_calls_RemoveROIWidget(self):
        self.trame_viewer.remove_roi()

        self.trame_viewer.cil_viewer.style.RemoveROIWidget.assert_called_once_with()

    def test_reset_defaults_resets_the_app_state(self):
        state["background_color"] = mock.MagicMock()
        state["slice"] = mock.MagicMock()
        state["orientation"] = mock.MagicMock()
        state["slice_window_range"] = mock.MagicMock()
        state["slice_window"] = mock.MagicMock()
        state["slice_level"] = mock.MagicMock()
        state["toggle_tracing"] = mock.MagicMock()
        state["toggle_interpolation"] = mock.MagicMock()
        default_slice = mock.MagicMock()
        self.trame_viewer.default_slice = default_slice
        slice_return = (random.random(), random.random())
        self.trame_viewer.cil_viewer.getSliceMapRange = mock.MagicMock(return_value=slice_return)

        self.trame_viewer.reset_defaults()

        self.assertEqual(state["background_color"], "cil_viewer_blue")
        self.assertEqual(state["slice"], default_slice)
        self.assertEqual(state["orientation"], f"{SLICE_ORIENTATION_XY}")
        self.trame_viewer.cil_viewer.getSliceMapRange.assert_called_once_with((5., 95.))
        self.assertEqual(state["slice_window_range"], slice_return)
        self.assertEqual(state["slice_window"], self.cil_viewer.getSliceColorWindow.return_value)
        self.assertEqual(state["slice_level"], self.cil_viewer.getSliceColorLevel.return_value)
        self.assertEqual(state["toggle_tracing"], False)
        self.assertEqual(state["toggle_interpolation"], False)

    def test_update_slice_data_sets_cmin_cmax_level_and_window(self):
        slice_return = (random.random(), random.random())
        self.trame_viewer.cil_viewer.getSliceMapRange = mock.MagicMock(return_value=slice_return)

        self.trame_viewer.update_slice_data()

        self.assertIn(call((5., 95.)), self.trame_viewer.cil_viewer.getSliceMapRange.call_args_list)
        self.assertIn(call((0., 100.)), self.trame_viewer.cil_viewer.getSliceMapRange.call_args_list)
        self.assertEqual(self.trame_viewer.cil_viewer.getSliceMapRange.call_count, 2)
        self.assertEqual(self.trame_viewer.cmin, slice_return[0])
        self.assertEqual(self.trame_viewer.cmax, slice_return[1])
        self.assertEqual(self.trame_viewer.slice_window_range_defaults, slice_return)
        self.assertEqual(self.trame_viewer.slice_level_default, self.cil_viewer.getSliceColorLevel.return_value)
        self.assertEqual(self.trame_viewer.slice_window_default, self.cil_viewer.getSliceColorWindow.return_value)
