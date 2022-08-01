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

from vtkmodules.util import colors

from ccpi.viewer.CILViewer2D import SLICE_ORIENTATION_XY, SLICE_ORIENTATION_XZ, SLICE_ORIENTATION_YZ
from ccpi.web_viewer.trame_viewer import TrameViewer, server, state


class TrameViewerTest(unittest.TestCase):
    # This test has the potential to be flaky on minor version numbers of trame, due to private API usage.
    def check_vuetify_default(self, object_to_check, expected_default):
        self.assertEqual(object_to_check._py_attr["v_model"][1], expected_default)

    @mock.patch("ccpi.web_viewer.trame_viewer.vtk")
    @mock.patch("ccpi.web_viewer.trame_viewer.TrameViewer.update_slice_data")
    def setUp(self, _, vtk_module):
        # Get the head data
        self.head_path = os.path.join(sys.prefix, 'share', 'cil', 'head.mha')
        self.file_list = [self.head_path, "other_file_path_dir/other_file"]

        # add the cil_viewer and defaults for a default __init__
        self.cil_viewer = mock.MagicMock()
        self.map_range = [0, 3790]
        self.cil_viewer.getSliceMapRange.return_value = self.map_range

        self.trame_viewer = TrameViewer(self.cil_viewer, self.file_list)

        # Assert on the mocks/patched objects after __init__
        vtk_module.VtkRemoteView.assert_called_once_with(self.cil_viewer.renWin, trame_server=server, ref="view")

    def test_trame_viewer_init_throws_when_list_of_files_is_none(self):
        with self.assertRaises(ValueError) as cm:
            TrameViewer(mock.MagicMock, None)
        self.assertEqual(str(cm.exception), "list_of_files cannot be None as we need data to load in the viewer!")

    def test_trame_viewer_default_file_selects_head_by_default(self):
        self.assertEqual(self.trame_viewer.default_file, self.head_path)

    @mock.patch("ccpi.web_viewer.trame_viewer.vtkMetaImageReader")  # for the loading
    @mock.patch("ccpi.web_viewer.trame_viewer.vtk")
    @mock.patch("ccpi.web_viewer.trame_viewer.TrameViewer.update_slice_data")
    def test_trame_viewer_default_file_select_first_in_list_if_no_head(self, _, __, ___):
        self.file_list = ["other_file_path_dir/other_file", "other_file_path_dir2/other_file2"]
        self.trame_viewer = TrameViewer(self.cil_viewer, self.file_list)

        self.assertEqual(self.trame_viewer.default_file, "other_file_path_dir/other_file")

    @mock.patch("ccpi.web_viewer.trame_viewer.TrameViewer.update_slice_data")
    @mock.patch("ccpi.web_viewer.trame_viewer.vtk")
    @mock.patch("ccpi.web_viewer.trame_viewer.TrameViewer.load_image")
    def test_trame_viewer_loads_default_file_initially(self, load_image, _, __):
        self.trame_viewer = TrameViewer(self.cil_viewer, self.file_list)

        load_image.assert_called_once_with(self.trame_viewer.default_file)

    def test_load_file_properly_uses_load_nexus_for_nexus_files(self):
        self.trame_viewer.load_nexus_file = mock.MagicMock()
        self.trame_viewer.load_image = mock.MagicMock()

        self.trame_viewer.load_file("file_path/file.nxs")

        self.trame_viewer.load_nexus_file.assert_called_once_with("file_path/file.nxs")
        self.trame_viewer.load_image.assert_not_called()

    def test_load_file_does_not_load_nexus_for_none_nexus_files(self):
        self.trame_viewer.load_nexus_file = mock.MagicMock()
        self.trame_viewer.load_image = mock.MagicMock()

        self.trame_viewer.load_file("file_path/file.mha")

        self.trame_viewer.load_nexus_file.assert_not_called()
        self.trame_viewer.load_image.assert_called_once_with("file_path/file.mha")

    def test_model_selector_list_is_generated_from_list_of_files_with_base_names_as_text_and_path_as_value(self):
        model_list = self.trame_viewer._create_model_selector_list()
        self.assertEqual(len(model_list), 2)
        self.assertEqual(model_list[0], {'text': 'head.mha', 'value': self.file_list[0]})
        self.assertEqual(model_list[1], {'text': 'other_file', 'value': self.file_list[1]})

    def test_model_create_model_selector_starts_with_default_file(self):
        model_selector = self.trame_viewer.create_model_selector()

        self.check_vuetify_default(model_selector, self.trame_viewer.default_file)

    def test_create_background_color_list_generate_properly(self):
        color_list = self.trame_viewer._create_background_color_list()
        # This changes with the number of VTK colors + 1 (miles_blue) - python defaults (__builtins__, __cached__ etc)
        self.assertEqual(len(color_list), len(dir(colors)) + 1 - 8)
        self.assertEqual(color_list[0], {
            "text": "Miles blue",
            "value": "cil_viewer_blue",
        })

    def test_create_background_selector_defaults_to_miles_blue(self):
        model_selector = self.trame_viewer.create_background_selector()

        self.check_vuetify_default(model_selector, "cil_viewer_blue")

    # This test has the potential to be flaky on minor version numbers of trame, due to private API usage.
    def test_create_slice_slider_min_max_default(self):
        self.trame_viewer.max_slice = mock.MagicMock()
        self.trame_viewer.default_slice = mock.MagicMock()
        slice_slider = self.trame_viewer.create_slice_slider()

        self.assertEqual(slice_slider._py_attr["min"], 0)
        self.assertEqual(slice_slider._py_attr["max"], self.trame_viewer.max_slice)
        self.check_vuetify_default(slice_slider, self.trame_viewer.default_slice)

    def test_create_toggle_details_button_starts_false(self):
        details_button = self.trame_viewer.create_toggle_window_details_button()

        self.check_vuetify_default(details_button, False)

    def test_create_auto_window_level_button(self):
        auto_button = self.trame_viewer.create_auto_window_level_button()
        text = "Auto Window/Level"

        self.assertIn(text, auto_button.html)
        self.assertEqual([text], auto_button.children)
        self.assertEqual(auto_button._py_attr["click"], self.trame_viewer.auto_window_level)

    def test_create_orientation_radio_buttons_has_3_orientations_and_defaults_to_XY(self):
        orientation_buttons = self.trame_viewer.create_orientation_radio_buttons()
        buttons_checked = 0
        for orientation_button in orientation_buttons.children:
            if 'label="XY"' in orientation_button.html:
                self.assertIn(f'value="{SLICE_ORIENTATION_XY}"', orientation_button.html)
            elif 'label=XZ' in orientation_button.html:
                self.assertIn(f'value="{SLICE_ORIENTATION_XZ}"', orientation_button.html)
            elif 'label=ZY' in orientation_button.html:
                self.assertIn(f'value="{SLICE_ORIENTATION_YZ}"', orientation_button.html)
            buttons_checked += 1
        self.assertEqual(buttons_checked, 3)
        self.check_vuetify_default(orientation_buttons, str(SLICE_ORIENTATION_XY))

    def test_construct_slice_window_sliders_use_percentages(self):
        self.trame_viewer.window_level_sliders_are_percentages = True
        self.trame_viewer.construct_slice_window_slider()
        slice_window_slider = self.trame_viewer.construct_slice_window_slider()
        self.assertIn('max="100"', slice_window_slider.html)
        self.assertIn('min="0"', slice_window_slider.html)
        self.assertIn('step="0.5"', slice_window_slider.html)
        self.check_vuetify_default(slice_window_slider, self.trame_viewer.slice_window_default)

    def test_construct_slice_window_sliders_do_not_use_percentages(self):
        self.trame_viewer.window_level_sliders_are_percentages = False
        self.trame_viewer.cmin = 0
        self.trame_viewer.cmax = 10
        slice_window_slider = self.trame_viewer.construct_slice_window_slider()

        self.assertIn(f'max="{self.trame_viewer.cmax}"', slice_window_slider.html)
        self.assertIn('min="0"', slice_window_slider.html)
        self.assertIn('step="1"', slice_window_slider.html)
        self.check_vuetify_default(slice_window_slider, self.trame_viewer.slice_window_default)

    def test_construct_slice_window_slider_shows_if_detailed_is_true(self):
        self.trame_viewer.slice_window_sliders_are_detailed = True
        self.trame_viewer.cmax = 1
        slice_window_slider = self.trame_viewer.construct_slice_window_slider()

        self.assertIn(f'style="max-width: 300px"', slice_window_slider.html)

    def test_construct_slice_window_slider_hides_if_detailed_is_false(self):
        self.trame_viewer.slice_window_sliders_are_detailed = False
        self.trame_viewer.cmax = 1
        slice_window_slider = self.trame_viewer.construct_slice_window_slider()

        self.assertIn(f'style="visibility: hidden; height: 0"', slice_window_slider.html)

    def test_construct_slice_level_slider_uses_percentage(self):
        self.trame_viewer.window_level_sliders_are_percentages = True
        self.trame_viewer.cmax = 1
        slice_level_slider = self.trame_viewer.construct_slice_level_slider()
        self.assertIn('max="100"', slice_level_slider.html)
        self.assertIn('min="0"', slice_level_slider.html)
        self.assertIn('step="0.5"', slice_level_slider.html)
        self.check_vuetify_default(slice_level_slider, self.trame_viewer.slice_level_default)

    def test_construct_slice_level_slider_does_not_use_percentage_when_cmax_more_than_100(self):
        self.trame_viewer.cmax = 102
        self.trame_viewer.cmin = 0
        self.trame_viewer.window_level_sliders_are_percentages = False
        slice_level_slider = self.trame_viewer.construct_slice_level_slider()

        self.assertIn(f'max="{self.trame_viewer.cmax}"', slice_level_slider.html)
        self.assertIn('min="0"', slice_level_slider.html)
        self.assertIn('step="1"', slice_level_slider.html)
        self.check_vuetify_default(slice_level_slider, self.trame_viewer.slice_level_default)

    def test_construct_slice_level_slider_shows_if_detailed_is_true(self):
        self.trame_viewer.slice_window_sliders_are_detailed = True
        self.trame_viewer.cmax = 1
        slice_level_slider = self.trame_viewer.construct_slice_level_slider()

        self.assertIn(f'style="max-width: 300px"', slice_level_slider.html)

    def test_construct_slice_level_slider_hides_if_detailed_is_false(self):
        self.trame_viewer.slice_window_sliders_are_detailed = False
        self.trame_viewer.cmax = 1
        slice_level_slider = self.trame_viewer.construct_slice_level_slider()

        self.assertIn(f'style="visibility: hidden; height: 0"', slice_level_slider.html)

    def test_construct_slice_window_range_slider_uses_percentage_when_cmax_less_than_100(self):
        self.trame_viewer.cmax = 1
        self.trame_viewer.window_level_sliders_are_percentages = True
        slice_window_slider = self.trame_viewer.construct_slice_window_range_slider()

        self.assertIn('max="100"', slice_window_slider.html)
        self.assertIn('min="0"', slice_window_slider.html)
        self.assertIn('step="0.5"', slice_window_slider.html)
        self.check_vuetify_default(slice_window_slider, self.trame_viewer.slice_window_default)

    def test_construct_slice_window_range_slider_does_not_use_percentage_when_cmax_more_than_100(self):
        self.trame_viewer.cmax = 102
        self.trame_viewer.cmin = 0
        self.trame_viewer.slice_window_range_defaults = self.map_range
        slice_window_range_slider = self.trame_viewer.construct_slice_window_range_slider()

        self.assertEqual(self.trame_viewer.window_level_sliders_are_percentages, False)
        self.assertIn(f'max="{self.trame_viewer.cmax}"', slice_window_range_slider.html)
        self.assertIn('min="0"', slice_window_range_slider.html)
        self.assertIn('step="1"', slice_window_range_slider.html)
        self.check_vuetify_default(slice_window_range_slider, self.map_range)

    def test_construct_slice_window_range_slider_shows_if_detailed_is_false(self):
        self.trame_viewer.slice_window_sliders_are_detailed = False
        self.trame_viewer.cmax = 1
        slice_window_range_slider = self.trame_viewer.construct_slice_window_range_slider()

        self.assertIn(f'style="max-width: 300px"', slice_window_range_slider.html)

    def test_construct_slice_window_range_slider_hides_if_detailed_is_true(self):
        self.trame_viewer.slice_window_sliders_are_detailed = True
        self.trame_viewer.cmax = 1
        slice_window_range_slider = self.trame_viewer.construct_slice_window_range_slider()

        self.assertIn(f'style="visibility: hidden; height: 0"', slice_window_range_slider.html)

    def test_update_slice_data_when_cmax_over_100(self):
        # over 100 means percentages are used
        get_image_map_range = [0, 101]
        self.cil_viewer.getImageMapRange.return_value = get_image_map_range

        self.trame_viewer.update_slice_data()

        self.assertEqual(self.trame_viewer.cmin, get_image_map_range[0])
        self.assertEqual(self.trame_viewer.cmax, get_image_map_range[1])
        self.assertEqual(self.trame_viewer.slice_window_range_defaults, get_image_map_range)
        self.assertEqual(self.trame_viewer.slice_level_default, self.cil_viewer.getSliceColorLevel.return_value)
        self.assertEqual(self.trame_viewer.slice_window_default, self.cil_viewer.getSliceColorWindow.return_value)

    def test_update_slice_data_when_cmax_under_100(self):
        # under 100 means values are used
        get_slice_map_range = [6, 89]
        get_image_map_range = [0, 99]
        self.cil_viewer.getSliceMapRange.return_value = get_slice_map_range
        self.cil_viewer.getImageMapRange.return_value = get_image_map_range

        self.trame_viewer.update_slice_data()

        self.assertEqual(self.trame_viewer.cmin, get_image_map_range[0])
        self.assertEqual(self.trame_viewer.cmax, get_image_map_range[1])
        self.assertEqual(self.trame_viewer.slice_window_range_defaults, [5., 95.])

        # TODO test default percentages:
        #self.assertEqual(self.trame_viewer.slice_level_default, self.cil_viewer.getSliceColorLevel.return_value)
        # self.assertEqual(self.trame_viewer.slice_window_default, self.cil_viewer.getSliceColorWindow.return_value)

    def test_update_slice_slider_data_updates_max_slice_and_default_slice(self):
        self.trame_viewer.cil_viewer.img3D.GetExtent.return_value = [0, 97, 0, 0, 0]
        self.trame_viewer.cil_viewer.sliceOrientation = 0

        self.trame_viewer.update_slice_slider_data()

        self.assertEqual(self.trame_viewer.max_slice, 97)
        self.assertEqual(self.trame_viewer.default_slice, 48)

    def test_change_background_changes_background_color_handles_miles_blue_in_cil_viewer(self):
        color_name = "cil_viewer_blue"
        color = (.1, .2, .4)

        self.trame_viewer.change_background_color(color_name)

        self.trame_viewer.cil_viewer.ren.SetBackground.assert_called_once_with(color)

    def test_change_background_changes_background_color_in_cil_viewer(self):
        color_name = "alice_blue"
        color = getattr(colors, color_name)

        self.trame_viewer.change_background_color(color_name)

        self.trame_viewer.cil_viewer.ren.SetBackground.assert_called_once_with(color)

    def test_switch_orientation_calls_change_orientation_in_cil_viewer(self):
        delattr(self.trame_viewer.cil_viewer.style, "ChangeOrientation")  # So we can test the hasattr statements
        self.trame_viewer.switch_to_orientation(SLICE_ORIENTATION_YZ)

        self.assertEqual(self.cil_viewer.sliceOrientation, SLICE_ORIENTATION_YZ)

        self.trame_viewer.cil_viewer.style.ChangeOrientation = mock.MagicMock()
        self.trame_viewer.switch_to_orientation(SLICE_ORIENTATION_XZ)

        self.trame_viewer.cil_viewer.style.ChangeOrientation.assert_called_once_with(SLICE_ORIENTATION_XZ)

    @mock.patch("ccpi.web_viewer.trame_viewer.vuetify.VSlider")
    @mock.patch("ccpi.web_viewer.trame_viewer.TrameViewer.update_slice_slider_data")
    def test_switch_orientation_calls_update_slice_slider_data(self, update_slice_slider_data, vslider):
        vslider_mock = mock.MagicMock()
        vslider.return_value = vslider_mock
        self.trame_viewer.slice_slider = mock.MagicMock()
        self.trame_viewer.construct_drawer_layout = mock.MagicMock()
        self.trame_viewer.layout.flush_content = mock.MagicMock()

        self.trame_viewer.switch_to_orientation(0)

        # Here the updates will happen
        update_slice_slider_data.assert_called_once()
        self.assertEqual(self.trame_viewer.slice_slider, vslider_mock)
        self.trame_viewer.construct_drawer_layout.assert_called_once()
        self.trame_viewer.layout.flush_content.assert_called_once()

    def test_change_window_level_detail_sliders_does_nothing_if_slice_window_sliders_are_detailed_is_false_and_passed_false(
            self):
        self.trame_viewer.slice_window_sliders_are_detailed = False

        self.cil_viewer.getSliceColorLevel.assert_not_called()
        self.cil_viewer.getSliceColorWindow.assert_not_called()

    def test_change_window_level_detail_sliders_sets_window_and_level_defaults_for_slices(self):
        self.trame_viewer.window_level_sliders_are_percentages = False
        current_window = 100
        current_level = 200
        self.trame_viewer.cil_viewer.getSliceColorLevel.return_value = current_level
        self.trame_viewer.cil_viewer.getSliceColorWindow.return_value = current_window
        expected_defaults = [150, 250]
        value_of_show_detailed = True

        self.trame_viewer.change_window_level_detail_sliders(value_of_show_detailed)

        self.assertEqual(self.trame_viewer.slice_window_range_defaults, expected_defaults)
        self.assertEqual(self.trame_viewer.slice_level_default, current_level)
        self.assertEqual(self.trame_viewer.slice_window_default, current_window)
        self.assertEqual(self.trame_viewer.slice_window_sliders_are_detailed, value_of_show_detailed)

        self.trame_viewer.window_level_sliders_are_percentages = True  # ------------------------------
        value_of_show_detailed = False

        self.trame_viewer.cmin = 0
        self.trame_viewer.cmax = 400

        self.trame_viewer.convert_value_to_percentage = mock.MagicMock()

        self.trame_viewer.change_window_level_detail_sliders(value_of_show_detailed)

        range_min = (current_window - 2 * current_level) / -2
        range_max = current_window + range_min
        self.trame_viewer.convert_value_to_percentage.assert_any_call(range_min)
        self.trame_viewer.convert_value_to_percentage.assert_any_call(range_max)
        self.trame_viewer.convert_value_to_percentage.assert_any_call(current_window)
        self.trame_viewer.convert_value_to_percentage.assert_any_call(current_level)
        self.assertEqual(self.trame_viewer.slice_window_sliders_are_detailed, value_of_show_detailed)

    def test_change_slice_window_level(self):
        win, level = 150, 200
        self.trame_viewer.change_slice_window_level(win, level)
        self.cil_viewer.setSliceColorWindowLevel.assert_called_once_with(win, level)

    def test_change_slice_window_level_percentiles(self):
        self.cil_viewer.setSliceColorPercentiles = mock.MagicMock()
        self.cil_viewer.setSliceMapRange = mock.MagicMock()
        min_pc, max_pc = [10, 20]
        self.trame_viewer.change_slice_window_level_percentiles(min_pc, max_pc)

        self.cil_viewer.setSliceMapRange.assert_not_called()
        self.cil_viewer.setSliceColorPercentiles.assert_called_once_with(min_pc, max_pc)

    def test_change_slice_window_level_range(self):
        self.cil_viewer.setSliceColorPercentiles = mock.MagicMock()
        self.cil_viewer.setSliceMapRange = mock.MagicMock()
        min, max = [10, 20]

        self.trame_viewer.change_slice_window_level_range(min, max)

        self.cil_viewer.setSliceColorPercentiles.assert_not_called()
        self.cil_viewer.setSliceMapRange.assert_called_once_with(min, max)

    def test_change_slice_window_as_percentage(self):
        self.cil_viewer.setSliceColorWindow = mock.MagicMock()
        self.trame_viewer.cmax = self.map_range[1]
        self.trame_viewer.cmin = self.map_range[0]

        expected_window = (self.map_range[1] + self.map_range[0]) / 2

        self.trame_viewer.change_slice_window_as_percentage(50)

        self.cil_viewer.setSliceColorWindow.assert_called_once_with(expected_window)

    def test_change_slice_window(self):
        self.cil_viewer.setSliceColorWindow = mock.MagicMock()
        window = 100
        self.trame_viewer.change_slice_window(window)
        self.cil_viewer.setSliceColorWindow.assert_called_once_with(window)

    def test_change_slice_level_as_percentage(self):
        self.trame_viewer.window_level_sliders_are_percentages = True
        self.cil_viewer.setSliceColorPercentiles = mock.MagicMock()
        self.cil_viewer.setSliceColorLevel = mock.MagicMock()
        self.trame_viewer.cmax = self.map_range[1]
        self.trame_viewer.cmin = self.map_range[0]
        level_pc = 50
        expected_level = (self.map_range[1] + self.map_range[0]) / 2
        self.trame_viewer.change_slice_level_as_percentage(level_pc)
        self.cil_viewer.setSliceColorLevel.assert_called_once_with(expected_level)

    def test_auto_window_level_values(self):
        self.trame_viewer.window_level_sliders_are_percentages = False
        state["slice_window_range"] = mock.MagicMock()
        state["slice_window"] = mock.MagicMock()
        state["slice_level"] = mock.MagicMock()
        cmin, cmax = 0, 90
        window, level = 50, 40
        self.cil_viewer.ia.GetAutoRange = mock.MagicMock(return_value=[cmin, cmax])
        self.cil_viewer.getSliceWindowLevelFromRange = mock.MagicMock(return_value=[window, level])

        self.trame_viewer.auto_window_level()

        self.assertEqual(state["slice_window_range"], (cmin, cmax))
        self.assertEqual(state["slice_window"], window)
        self.assertEqual(state["slice_level"], level)
        self.cil_viewer.ia.GetAutoRange.assert_called_once()
        self.cil_viewer.getSliceWindowLevelFromRange.assert_called_once_with(cmin, cmax)

    def test_auto_window_level_as_percentage(self):
        self.trame_viewer.window_level_sliders_are_percentages = True
        state["slice_window_range_percentiles"] = mock.MagicMock()
        state["slice_window_as_percentage"] = mock.MagicMock()
        state["slice_level_as_percentage"] = mock.MagicMock()

        cmin, cmax = 0, 90
        window, level = 50, 40
        pmin, pmax = 0, 70
        pwindow, plevel = 45, 48
        self.cil_viewer.ia = mock.MagicMock()
        self.cil_viewer.ia.GetAutoRange = mock.MagicMock(return_value=[cmin, cmax])
        self.cil_viewer.getSliceWindowLevelFromRange = mock.MagicMock(return_value=[window, level])
        self.cil_viewer.ia.GetAutoRangePercentiles = mock.MagicMock(return_value=[pmin, pmax])
        self.trame_viewer.convert_value_to_percentage = mock.MagicMock()
        # sets the return values for each call:
        self.trame_viewer.convert_value_to_percentage.side_effect = [pwindow, plevel]

        self.trame_viewer.auto_window_level()

        self.assertEqual(state["slice_window_percentiles"], self.cil_viewer.ia.GetAutoRangePercentiles.return_value)
        self.assertEqual(state["slice_window_as_percentage"], pwindow)
        self.assertEqual(state["slice_level_as_percentage"], plevel)
        self.cil_viewer.ia.GetAutoRange.assert_called_once()
        self.cil_viewer.getSliceWindowLevelFromRange.assert_called_once_with(cmin, cmax)
        self.cil_viewer.ia.GetAutoRangePercentiles.assert_called_once()
        self.trame_viewer.convert_value_to_percentage.assert_any_call(level)
        self.trame_viewer.convert_value_to_percentage.assert_any_call(window)

    def test_convert_value_to_percentage_and_convert_percentage_to_value(self):
        self.trame_viewer.cmax = self.map_range[1]
        self.trame_viewer.cmin = self.map_range[0]
        value = 50
        expected_percentage = 100 * (value - self.map_range[0]) / (self.map_range[0] + self.map_range[1])
        returned_percentage = self.trame_viewer.convert_value_to_percentage(value)
        self.assertEqual(returned_percentage, expected_percentage)
        self.assertEqual(self.trame_viewer.convert_percentage_to_value(returned_percentage), value)

    def test_change_slice_level(self):
        self.cil_viewer.setSliceColorLevel = mock.MagicMock()
        level = 200

        self.trame_viewer.change_slice_level(level)

        self.cil_viewer.setSliceColorLevel.assert_called_once_with(level)

    def test_change_slice_number_raises_error(self):
        with self.assertRaises(NotImplementedError) as cm:
            self.trame_viewer.change_slice_number(0)
        self.assertEqual(
            str(cm.exception),
            "This function is not implemented in the base class, but you can expect an implementation in "
            "it's sub classes.")

    def test_reset_defaults_raises_error(self):
        with self.assertRaises(NotImplementedError) as cm:
            self.trame_viewer.reset_defaults()
        self.assertEqual(
            str(cm.exception),
            "This function is not implemented in the base class, but you can expect an implementation in "
            "it's sub classes.")

    def test_construct_drawer_layout_raises_error(self):
        with self.assertRaises(NotImplementedError) as cm:
            self.trame_viewer.construct_drawer_layout()
        self.assertEqual(
            str(cm.exception),
            "This function is not implemented in the base class, but you can expect an implementation in "
            "it's sub classes.")

    def test_create_drawer_ui_elements_raises_error(self):
        with self.assertRaises(NotImplementedError) as cm:
            self.trame_viewer.create_drawer_ui_elements()
        self.assertEqual(
            str(cm.exception),
            "This function is not implemented in the base class, but you can expect an implementation in "
            "it's sub classes.")

    def test_show_slice_histogram_will_set_the_state_of_histogramPlotActor(self):
        self.trame_viewer.show_slice_histogram(True)

        self.trame_viewer.cil_viewer.updateSliceHistogram.assert_called_once()
        self.trame_viewer.cil_viewer.histogramPlotActor.VisibilityOn.assert_called_once()

        self.trame_viewer.show_slice_histogram(False)

        self.trame_viewer.cil_viewer.histogramPlotActor.VisibilityOff.assert_called_once()
        self.trame_viewer.cil_viewer.histogramPlotActor.VisibilityOn.assert_called_once()
