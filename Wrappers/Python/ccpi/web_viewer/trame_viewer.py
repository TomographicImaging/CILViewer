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

from trame.app import get_server
from trame.widgets import vtk, vuetify
from trame.ui.vuetify import SinglePageWithDrawerLayout
from vtkmodules.util import colors
from vtkmodules.vtkIOImage import vtkMetaImageReader

from ccpi.viewer.CILViewer2D import SLICE_ORIENTATION_XY, SLICE_ORIENTATION_XZ, SLICE_ORIENTATION_YZ
from ccpi.viewer.utils.conversion import cilHDF5ResampleReader

server = get_server()
state, ctrl = server.state, server.controller


class TrameViewer:
    """
    This class is intended as a base class and not to be used outside of one of the TrameViewer2D and TrameViewer3D classes.
    """

    def __init__(self, viewer_class, list_of_files: list = None):
        # Load files and setup the CILViewer
        if list_of_files is None:
            raise AttributeError("list_of_files cannot be None as we need data to load in the viewer!")
        self.list_of_files = list_of_files

        self.default_file = None
        for file_path in self.list_of_files:
            if "head.mha" in file_path:
                self.default_file = file_path
                break
        if self.default_file is None:
            self.default_file = list_of_files[0]

        # Create the relevant CILViewer
        self.cil_viewer = viewer_class()
        self.load_file(self.default_file)

        # Set the defaults of the base class state
        self.max_slice = None
        self.default_slice = None
        # Set slice slider data:
        self.update_slice_slider_data()
        # Continue with defaults
        self.cmin = None
        self.cmax = None
        self.slice_window_default = None
        self.slice_level_default = None
        self.slice_window_range_defaults = None
        # Set slice info into the current state min, max, and some defaults:
        self.update_slice_data()
        self.slice_window_sliders_are_detailed = False
        self.window_level_sliders_are_percentages = False

        self.html_view = vtk.VtkRemoteView(self.cil_viewer.renWin, trame_server=server, ref="view")
        ctrl.view_update = self.html_view.update
        ctrl.view_reset_camera = self.html_view.reset_camera
        ctrl.on_server_ready.add(self.html_view.update)

        # Create page title using the class name of the viewer so it changes based on whatever is passed to this class
        page_title = f"{viewer_class.__name__} on web"
        self.layout = SinglePageWithDrawerLayout(server, on_ready=self.html_view.update, width=300)
        self.layout.title.set_text(page_title)

    def start(self):
        # Could be static but we don't want it to start from just the class, so must be called on a constructed object where __init__
        # has ran.
        server.start()

    def load_file(self, file_name: str, windowing_method: str = "scalar"):
        if "data" not in file_name:
            file_name = os.path.join("data", file_name)
        if ".nxs" in file_name:
            self.load_nexus_file(file_name)
        else:
            self.load_image(file_name)

    def load_image(self, image_file: str):
        reader = vtkMetaImageReader()
        reader.SetFileName(image_file)
        reader.Update()
        self.cil_viewer.setInput3DData(reader.GetOutput())

    def load_nexus_file(self, file_name: str):
        reader = cilHDF5ResampleReader()
        reader.SetFileName(file_name)
        reader.SetDatasetName('entry1/tomo_entry/data/data')
        reader.SetTargetSize(256 * 256 * 256)
        reader.Update()
        self.cil_viewer.setInput3DData(reader.GetOutput())

    def create_model_selector(self):
        useful_file_list = []
        for file_path in self.list_of_files:
            file_name = os.path.basename(file_path)
            useful_file_list.append({"text": file_name, "value": file_path})

        return vuetify.VSelect(
            v_model=("file_name", self.default_file),
            items=("file_name_options", useful_file_list),
            hide_details=True,
            solo=True,
        )

    def create_background_selector(self):
        initial_list = dir(colors)
        color_list = [{
            "text": "Miles blue",
            "value": "cil_viewer_blue",
        }]
        for color in initial_list:
            if "__" in color:
                continue
            if "_" in color:
                filtered_color = color.replace("_", " ")
            else:
                filtered_color = color
            filtered_color = filtered_color.capitalize()
            color_list.append({"text": filtered_color, "value": color})
        return vuetify.VSelect(v_model=("background_color", "cil_viewer_blue"),
                               items=("background_color_options", color_list),
                               hide_details=True,
                               solo=True)

    def create_slice_slider(self, disabled: bool = False):
        return vuetify.VSlider(v_model=("slice", self.default_slice),
                               min=0,
                               max=self.max_slice,
                               step=1,
                               hide_details=True,
                               dense=True,
                               label="Slice",
                               thumb_label=True,
                               disabled=disabled,
                               style="max-width: 300px")

    def create_toggle_window_details_button(self, disabled: bool = False):
        return vuetify.VSwitch(
            v_model=("slice_detailed_sliders", False),
            label="Detailed window/level sliders",
            hide_details=True,
            dense=True,
            disabled=disabled,
            solo=True,
        )

    def create_auto_window_level_button(self, disabled: bool = False):
        return vuetify.VBtn("Auto Window/Level",
                            hide_details=True,
                            dense=True,
                            solo=True,
                            disabled=disabled,
                            click=self.auto_window_level)

    def create_orientation_radio_buttons(self, disabled: bool = False):
        return vuetify.VRadioGroup(
            children=[
                vuetify.VRadio(label="XY", value=f"{SLICE_ORIENTATION_XY}"),
                vuetify.VRadio(label="XZ", value=f"{SLICE_ORIENTATION_XZ}"),
                vuetify.VRadio(label="ZY", value=f"{SLICE_ORIENTATION_YZ}"),
            ],
            v_model=("orientation", f"{SLICE_ORIENTATION_XY}"),
            label="Slice orientation:",
            disabled=disabled,
        )

    def construct_slice_window_slider(self, disabled: bool = False):
        if not self.window_level_sliders_are_percentages:
            # Use actual value
            min_value = self.cmin
            max_value = self.cmax
            step = 1
            v_model = ("slice_window", self.slice_window_default)
        else:
            # Use percentages
            min_value = 0
            max_value = 100
            step = 0.5
            v_model=("slice_window_as_percentage",  self.slice_window_default)

        if self.slice_window_sliders_are_detailed:
            style = "max-width: 300px"
        else:
            style = "visibility: hidden; height: 0"

        return vuetify.VSlider(v_model=v_model,
                               min=min_value,
                               max=max_value,
                               step=step,
                               hide_details=True,
                               disabled=disabled,
                               dense=True,
                               label="Slice window",
                               thumb_label=True,
                               style=style)

    def construct_slice_level_slider(self, disabled: bool = False):
        if not self.window_level_sliders_are_percentages:
            # Use actual value
            min_value = self.cmin
            max_value = self.cmax
            step = 1
            v_model = ("slice_level", self.slice_level_default)
        else:
            # Use percentages
            min_value = 0
            max_value = 100
            step = 0.5
            v_model = ("slice_level_as_percentage", self.slice_level_default)

        if self.slice_window_sliders_are_detailed:
            style = "max-width: 300px"
        else:
            style = "visibility: hidden; height: 0"

        return vuetify.VSlider(v_model=v_model,
                               min=min_value,
                               max=max_value,
                               step=step,
                               hide_details=True,
                               dense=True,
                               disabled=disabled,
                               label="Slice level",
                               thumb_label=True,
                               style=style)

    def construct_slice_window_range_slider(self, disabled: bool = False):
        if not self.window_level_sliders_are_percentages:
            # Use actual values
            min_value = self.cmin
            max_value = self.cmax
            step = 1
            v_model = ("slice_window_range", self.slice_window_range_defaults)
        else:
            # Use percentages
            min_value = 0
            max_value = 100
            step = 0.5
            v_model=("slice_window_percentiles", self.slice_window_range_defaults)

        if not self.slice_window_sliders_are_detailed:
            style = "max-width: 300px"
        else:
            style = "visibility: hidden; height: 0"

        return vuetify.VRangeSlider(
            v_model=v_model,
            min=min_value,
            max=max_value,
            step=step,
            hide_details=True,
            dense=True,
            disabled=disabled,
            label="Slice window",
            thumb_label=True,
            style=style,
        )

    def update_slice_data(self):
        self.cmin, self.cmax = self.cil_viewer.getImageMapRange((0., 100.), "scalar")

        if self.cmax > 100:
            self.window_level_sliders_are_percentages = False
            self.slice_window_range_defaults = self.cil_viewer.getImageMapRange((5., 95.), "scalar")
            self.slice_level_default = self.cil_viewer.getSliceColorLevel()
            self.slice_window_default = self.cil_viewer.getSliceColorWindow()
        else:
            self.window_level_sliders_are_percentages = True
            self.slice_window_range_defaults = [5., 95.]
            self.slice_level_default = self.convert_value_to_percentage(self.cil_viewer.getSliceColorLevel())
            self.slice_window_default = self.convert_value_to_percentage(self.cil_viewer.getSliceColorWindow())

    def update_slice_slider_data(self):
        self.max_slice = self.cil_viewer.img3D.GetExtent()[self.cil_viewer.sliceOrientation * 2 + 1]
        self.default_slice = round(self.max_slice / 2)

    def change_background_color(self, color: str):
        if color == "cil_viewer_blue":
            color_data = (.1, .2, .4)
        else:
            color_data = getattr(colors, color.lower())
        self.cil_viewer.ren.SetBackground(color_data)
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def switch_to_orientation(self, slice_orientation: int):
        if hasattr(self.cil_viewer.style, "ChangeOrientation"):
            self.cil_viewer.style.ChangeOrientation(slice_orientation)
        else:
            self.cil_viewer.sliceOrientation = slice_orientation
        # Update the slice slider when orientation changes as the number of slices changes
        self.update_slice_slider_data()
        if hasattr(self, "slice_slider") and self.slice_slider is not None:
            self.slice_slider = vuetify.VSlider(v_model=("slice", self.default_slice),
                                                min=0,
                                                max=self.max_slice,
                                                step=1,
                                                hide_details=True,
                                                dense=True,
                                                label="Slice",
                                                thumb_label=True,
                                                style="max-width: 300px")
            self.construct_drawer_layout()
            self.layout.flush_content()
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def change_window_level_detail_sliders(self, show_detailed: bool):
        if show_detailed == self.slice_window_sliders_are_detailed:
            return
        # Translate current color level and color window to range_min and range_max
        current_level = self.cil_viewer.getSliceColorLevel()
        current_window = self.cil_viewer.getSliceColorWindow()
        range_min = (current_window - 2 * current_level
                     ) / -2  # The reverse of the window calculation in web_app.change_slice_window_level_range
        range_max = current_window + range_min

        # Setup the defaults pre-flip between detailed / not detailed:
        if not self.window_level_sliders_are_percentages:
            self.slice_window_range_defaults = [range_min, range_max]
            self.slice_level_default = current_level
            self.slice_window_default = current_window
        else:
            self.slice_window_range_defaults = [self.convert_value_to_percentage(range_min), self.convert_value_to_percentage(range_max)]
            self.slice_level_default = self.convert_value_to_percentage(current_level)
            self.slice_window_default = self.convert_value_to_percentage(current_window)

        # Toggle the detailed sliders
        self.slice_window_sliders_are_detailed = show_detailed

    def change_slice_window_level(self, window: float, level: float):
        self.cil_viewer.setSliceColorWindowLevel(window, level)
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def change_slice_window_level_range(self, min: float, max: float):
        self.cil_viewer.setSliceMapRange(min, max)
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def change_slice_window_level_percentiles(self, min: float, max: float):
        self.cil_viewer.setSliceColorPercentiles(min, max)
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def change_slice_window(self, new_window: float):
        self.cil_viewer.setSliceColorWindow(new_window)
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def change_slice_window_as_percentage(self, new_window_as_percentage: float):
        window = self.convert_percentage_to_value(new_window_as_percentage)
        self.change_slice_window(window)

    def change_slice_level(self, new_level: float):
        self.cil_viewer.setSliceColorLevel(new_level)
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def change_slice_level_as_percentage(self, new_level_as_percentage: float):
        level = self.convert_percentage_to_value(new_level_as_percentage)
        self.change_slice_level(level)

    def auto_window_level(self):
        cmin, cmax = self.cil_viewer.ia.GetAutoRange()
        window, level = self.cil_viewer.getSliceWindowLevelFromRange(cmin, cmax)
        if self.window_level_sliders_are_percentages:
            state["slice_window_percentiles"] = self.cil_viewer.ia.GetAutoRangePercentiles()
            state["slice_window_as_percentage"] = self.convert_value_to_percentage(window)
            state["slice_level_as_percentage"] = self.convert_value_to_percentage(level)
        else:
            state["slice_window_range"] = cmin, cmax
            state["slice_window"] = window
            state["slice_level"] = level
        self.cil_viewer.updatePipeline()

    def convert_value_to_percentage(self, value):
        # Takes into account that self.cmin may not be 0:
        percentage = 100 * (value - self.cmin) / (self.cmax + self.cmin)
        return percentage

    def convert_percentage_to_value(self, percentage):
        # Takes into account that self.cmin may not be 0:
        value = percentage * (self.cmax + self.cmin) / 100 + self.cmin
        return value

    def change_slice_number(self, slice_number):
        if hasattr(self.cil_viewer, "updateSliceHistogram"):
            self.cil_viewer.updateSliceHistogram()
        self.cil_viewer.setActiveSlice(slice_number)
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def construct_drawer_layout(self):
        raise NotImplementedError(
            "This function is not implemented in the base class, but you can expect an implementation in it's sub"
            " classes.")

    def create_drawer_ui_elements(self):
        raise NotImplementedError(
            "This function is not implemented in the base class, but you can expect an implementation in it's sub"
            " classes.")

    def show_slice_histogram(self, show_histogram):
        self.cil_viewer.updateSliceHistogram()
        if show_histogram:
            self.cil_viewer.histogramPlotActor.VisibilityOn()
        else:
            self.cil_viewer.histogramPlotActor.VisibilityOff()
        self.html_view.update()
