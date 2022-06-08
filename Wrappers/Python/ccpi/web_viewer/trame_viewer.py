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
from typing import Union, TYPE_CHECKING

from trame.html import vtk, vuetify
from trame.layouts import SinglePageWithDrawer
from vtkmodules.util import colors
from vtkmodules.vtkIOImage import vtkMetaImageReader

from ccpi.viewer.CILViewer2D import SLICE_ORIENTATION_XY, SLICE_ORIENTATION_XZ, SLICE_ORIENTATION_YZ
from ccpi.viewer.utils.conversion import cilHDF5ResampleReader


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
        self.slice_window_slider_is_percentage = False

        self.html_view = vtk.VtkRemoteView(self.cil_viewer.renWin)

        # Create page title using the class name of the viewer so it changes based on whatever is passed to this class
        page_title = f"{viewer_class.__name__} on web"
        self.layout = SinglePageWithDrawer(page_title, on_ready=self.html_view.update, width=300)
        self.layout.title.set_text(page_title)
        self.layout.logo.children = [vuetify.VIcon("mdi-skull", classes="mr-4")]

    def start(self):
        self.layout.start()

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
            useful_file_list.append(
                {
                    "text": file_name,
                    "value": file_path
                }
            )

        return vuetify.VSelect(
            v_model=("file_name", self.default_file),
            items=("file_name_options", useful_file_list),
            hide_details=True,
            solo=True,
        )

    def create_background_selector(self):
        initial_list = dir(colors)
        color_list = [
            {
                "text": "Miles blue",
                "value": "cil_viewer_blue",
            }
        ]
        for color in initial_list:
            if "__" in color:
                continue
            if "_" in color:
                filtered_color = color.replace("_", " ")
            else:
                filtered_color = color
            filtered_color = filtered_color.capitalize()
            color_list.append(
                {
                    "text": filtered_color,
                    "value": color
                }
            )
        return vuetify.VSelect(
            v_model=("background_color", "cil_viewer_blue"),
            items=("background_color_options", color_list),
            hide_details=True,
            solo=True
        )

    def create_slice_slider(self, disabled: bool = False):
        return vuetify.VSlider(
            v_model=("slice", self.default_slice),
            min=0,
            max=self.max_slice,
            step=1,
            hide_details=True,
            dense=True,
            label="Slice",
            thumb_label=True,
            disabled=disabled,
            style="max-width: 300px"
        )

    def create_toggle_window_details_button(self, disabled: bool = False):
        return vuetify.VSwitch(
            v_model=("slice_detailed_sliders", False),
            label="Detailed window/level sliders",
            hide_details=True,
            dense=True,
            disabled=disabled,
            solo=True,
        )

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
        if self.cmax > 100:
            # Use actual value
            min_value = self.cmin
            max_value = self.cmax
            step = 1
            self.slice_window_slider_is_percentage = False
        else:
            # Use percentages
            min_value = 0
            max_value = 100
            step = 0.5
            self.slice_window_slider_is_percentage = True

        if self.slice_window_sliders_are_detailed:
            style = "max-width: 300px"
        else:
            style = "visibility: hidden; height: 0"

        return vuetify.VSlider(
            v_model=("slice_window", self.slice_window_default),
            min=min_value,
            max=max_value,
            step=step,
            hide_details=True,
            disabled=disabled,
            dense=True,
            label="Slice window",
            thumb_label=True,
            style=style
        )

    def construct_slice_level_slider(self, disabled: bool = False):
        if self.cmax > 100:
            # Use actual value
            min_value = self.cmin
            max_value = self.cmax
            step = 1
            self.slice_level_slider_is_percentage = False
        else:
            # Use percentages
            min_value = 0
            max_value = 100
            step = 0.5
            self.slice_level_slider_is_percentage = True

        if self.slice_window_sliders_are_detailed:
            style = "max-width: 300px"
        else:
            style = "visibility: hidden; height: 0"

        return vuetify.VSlider(
            v_model=("slice_level", self.slice_level_default),
            min=min_value,
            max=max_value,
            step=step,
            hide_details=True,
            dense=True,
            disabled=disabled,
            label="Slice level",
            thumb_label=True,
            style=style
        )

    def construct_slice_window_range_slider(self, disabled: bool = False):
        if self.cmax > 100:
            # Use actual values
            min_value = self.cmin
            max_value = self.cmax
            step = 1
            self.slice_window_slider_is_percentage = False
        else:
            # Use percentages
            min_value = 0
            max_value = 100
            step = 0.5
            self.slice_window_slider_is_percentage = True

        if not self.slice_window_sliders_are_detailed:
            style = "max-width: 300px"
        else:
            style = "visibility: hidden; height: 0"

        return vuetify.VRangeSlider(
            v_model=("slice_window_range", self.slice_window_range_defaults),
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
        if hasattr(self.cil_viewer, "getSliceMapWindow"):
            self.cmin, self.cmax = self.cil_viewer.getSliceMapWindow((0., 100.))
            self.slice_window_range_defaults = self.cil_viewer.getSliceMapWindow((5., 95.))
        else:
            self.cmin, self.cmax = self.cil_viewer.getVolumeMapWindow((0., 100.), "scalar")
            self.slice_window_range_defaults = self.cil_viewer.getVolumeMapWindow((5., 95.), "scalar")
        self.slice_level_default = self.cil_viewer.getSliceColorLevel()
        self.slice_window_default = self.cil_viewer.getSliceColorWindow()

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
        self.cil_viewer.sliceOrientation = slice_orientation
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def change_window_level_detail_sliders(self, show_detailed: bool):
        if show_detailed == self.slice_window_sliders_are_detailed:
            return
        # Translate current color level and color window to range_min and range_max
        current_level = self.cil_viewer.getSliceColorLevel()
        current_window = self.cil_viewer.getSliceColorWindow()
        range_min = (current_window - 2 * current_level) / -2  # The reverse of the window calculation in web_app.change_slice_window_level
        range_max = current_window + range_min

        # Setup the defaults pre-flip
        self.slice_window_range_defaults = [range_min, range_max]
        self.slice_level_default = current_level
        self.slice_window_default = current_window

        # Toggle the detailed sliders
        self.slice_window_sliders_are_detailed = show_detailed

    def change_slice_window_range(self, window: float, level: float):
        if hasattr(self.cil_viewer, "setSliceColorWindowLevel"):
            self.cil_viewer.setSliceColorWindowLevel(window, level)
        else:
            self.cil_viewer.setColorWindowLevel(window, level)
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def change_slice_window(self, new_window: float):
        if hasattr(self.cil_viewer, "setSliceColorWindow"):
            self.cil_viewer.setSliceColorWindow(window=new_window)
        else:
            self.cil_viewer.setColorWindow(window=new_window)
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def change_slice_level(self, new_level: float):
        if hasattr(self.cil_viewer, "setSliceColorLevel"):
            self.cil_viewer.setSliceColorLevel(level=new_level)
        else:
            self.cil_viewer.setColorLevel(level=new_level)
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def construct_drawer_layout(self):
        raise NotImplementedError("This function is not implemented in the base class, but you can expect an implementation in it's sub"
                                  " classes.")

    def create_drawer_ui_elements(self):
        raise NotImplementedError("This function is not implemented in the base class, but you can expect an implementation in it's sub"
                                  " classes.")
