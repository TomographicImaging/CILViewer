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

try:
    import matplotlib.pyplot as plt
except ImportError:
    # Add optional overload to allow plt.colormaps to be called without matplotlib
    from ccpi.viewer.utils import CILColorMaps

    class BackupColorMaps:

        @staticmethod
        def colormaps():
            return ['viridis', 'plasma', 'inferno', 'magma']

    plt = BackupColorMaps()

from trame import update_layout
from trame.html import vtk, vuetify
from trame.layouts import SinglePageWithDrawer
from vtkmodules.util import colors
from vtkmodules.vtkIOImage import vtkMetaImageReader

from ccpi.viewer.CILViewer import CILViewer
from ccpi.viewer.CILViewer2D import SLICE_ORIENTATION_XY, SLICE_ORIENTATION_XZ, SLICE_ORIENTATION_YZ
from ccpi.viewer.utils.conversion import cilHDF5ResampleReader
from ccpi.web_viewer.camera_data import CameraData

DEFAULT_SLICE = 32
INITIAL_IMAGE = "head.mha"


class TrameViewer:

    def __init__(self, list_of_files=None):
        # Define attributes that will be constructed in methods outside of __init__
        self.cmin = None
        self.cmax = None
        self.windowing_defaults = None
        self.slice_window_range_defaults = None
        self.slice_level_default = None
        self.slice_window_default = None
        self.max_slice = None
        self.default_slice = None
        self.slice_interaction_col = None
        self.slice_interaction_row = None
        self.slice_interaction_section = None
        self.volume_interaction_col = None
        self.volume_interaction_row = None
        self.volume_interaction_section = None
        self.windowing_slider_is_percentage = False  # Defaults to not percentage with the head.mha file
        self.color_slider_is_percentage = False  # Defaults to not percentage with the head.mha file
        self.slice_level_slider_is_percentage = False  # Defaults to not percentage with the head.mha file
        self.slice_window_slider_is_percentage = False  # Defaults to not percentage with the head.mha file
        self.slice_window_sliders_are_detailed = False  # Defaults to none-detailed sliders
        self.disable_2d = False
        self.disable_3d = False

        # Define UI elements in __init__ to quiet down Pep8
        self.model_choice = None
        self.background_choice = None
        self.toggle_slice_visibility = None
        self.slice_slider = None
        self.toggle_window_details_button = None
        self.orientation_radio_buttons = None
        self.slice_window_range_slider = None
        self.slice_window_slider = None
        self.slice_level_slider = None
        self.show_slice_histogram_switch = None
        self.toggle_volume_visibility = None
        self.opacity_radio_buttons = None
        self.color_choice = None
        self.clipping_switch = None
        self.clipping_removal_button = None
        self.color_slider = None
        self.windowing_range_slider = None
        self.reset_cam_button = None
        self.reset_defaults_button = None

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

        self.cil_viewer = CILViewer()
        self.load_file(self.default_file, first_load=True)

        self.html_view = vtk.VtkRemoteView(
            self.cil_viewer.renWin,
            # interactor_events=("events", 'KeyPress'),
            # KeyPress=(self.on_key_press, "[$event.keyCode]"),
        )
        self.set_opacity_mapping("scalar")
        self.switch_render()  # Turn on 3D view by default

        # Grab current pos and orientation for reset later.
        self.original_cam_data = CameraData(self.cil_viewer.ren.GetActiveCamera())

        self.layout = SinglePageWithDrawer("CILViewer on web", on_ready=self.html_view.update, width=300)
        self.layout.title.set_text("CILViewer on Web")
        self.layout.logo.children = [vuetify.VIcon("mdi-skull", classes="mr-4")]

        self.update_slice_data()

        self.create_drawer_ui_elements()

        self.construct_drawer_layout()

        self.layout.children += [
            vuetify.VContainer(
                fluid=True,
                classes="pa-0 fill-height",
                children=[self.html_view],
            )
        ]

        # Setup default state
        self.set_default_button_state()

    def construct_drawer_layout(self):
        # The difference is that we use range slider instead of detailed sliders
        self.slice_interaction_col = vuetify.VCol([
            self.toggle_slice_visibility, self.slice_slider, self.orientation_radio_buttons,
            self.show_slice_histogram_switch, self.toggle_window_details_button, self.slice_window_range_slider,
            self.slice_window_slider, self.slice_level_slider
        ])
        self.slice_interaction_row = vuetify.VRow(self.slice_interaction_col)
        self.slice_interaction_section = vuetify.VContainer(self.slice_interaction_row)

        self.volume_interaction_col = vuetify.VCol([
            self.toggle_volume_visibility, self.opacity_radio_buttons, self.color_choice, self.color_slider,
            self.clipping_switch, self.clipping_removal_button, self.windowing_range_slider
        ])
        self.volume_interaction_row = vuetify.VRow(self.volume_interaction_col)
        self.volume_interaction_section = vuetify.VContainer(self.volume_interaction_row)

        self.layout.drawer.children = [
            "Choose model to load", self.model_choice,
            vuetify.VDivider(), "Choose background color", self.background_choice,
            vuetify.VDivider(), self.slice_interaction_section,
            vuetify.VDivider(), self.volume_interaction_section,
            vuetify.VDivider(), self.reset_cam_button,
            vuetify.VDivider(), self.reset_defaults_button
        ]

    def create_drawer_ui_elements(self):
        # replace this with the list browser? # https://kitware.github.io/trame/docs/module-widgets.html#ListBrowser
        self.model_choice = self.create_model_selector()
        self.background_choice = self.create_background_selector()
        self.toggle_slice_visibility = self.create_toggle_slice_visibility()
        self.slice_slider = self.create_slice_slider()
        self.toggle_window_details_button = self.create_toggle_window_details_button()
        self.orientation_radio_buttons = self.create_orientation_radio_buttons()
        self.slice_window_range_slider = self.construct_slice_window_range_slider()
        self.slice_window_slider = self.construct_slice_window_slider()
        self.slice_level_slider = self.construct_slice_level_slider()
        self.show_slice_histogram_switch = self.construct_show_slice_histogram_switch()
        self.toggle_volume_visibility = self.create_toggle_volume_visibility()
        self.opacity_radio_buttons = self.create_opacity_radio_buttons()
        self.color_choice = self.create_color_choice_selector()
        self.clipping_switch = self.create_clipping_toggle()
        self.clipping_removal_button = self.create_clipping_removal_button()
        self.update_windowing_defaults()
        self.color_slider = self.construct_color_slider()
        self.windowing_range_slider = self.construct_windowing_slider()
        self.reset_cam_button = self.create_reset_camera_button()
        self.reset_defaults_button = self.create_reset_defaults_button()

    def construct_show_slice_histogram_switch(self):
        return vuetify.VSwitch(
            label="Show slice histogram",
            v_model=("show_slice_histogram", False),
            hide_details=True,
            dense=True,
            solo=True,
            disabled=self.disable_2d,
        )

    def create_reset_defaults_button(self):
        return vuetify.VBtn("Reset defaults", hide_details=True, dense=True, solo=True, click=self.reset_defaults)

    def create_reset_camera_button(self):
        return vuetify.VBtn(
            "Reset Camera",
            hide_details=True,
            dense=True,
            solo=True,
            click=self.reset_cam,
        )

    def create_clipping_toggle(self):
        return vuetify.VSwitch(
            label="Toggle Clipping",
            v_model=("toggle_clipping", False),
            hide_details=True,
            dense=True,
            solo=True,
            disabled=self.disable_3d,
        )

    def create_clipping_removal_button(self):
        return vuetify.VBtn("Remove clipping",
                            hide_details=True,
                            dense=True,
                            solo=True,
                            disabled=self.disable_3d,
                            click=self.remove_clipping_plane)

    def create_color_choice_selector(self):
        return vuetify.VSelect(
            v_model=("color_map", "viridis"),
            items=("color_map_options", plt.colormaps()),
            hide_details=True,
            solo=True,
            disabled=self.disable_3d,
        )

    def create_opacity_radio_buttons(self):
        return vuetify.VRadioGroup(
            children=[
                vuetify.VRadio(ref="opacity_scalar_button", label="Scalar", value="scalar"),
                vuetify.VRadio(label="Gradient", value="gradient"),
            ],
            v_model=("opacity", "scalar"),
            label="Opacity mapping:",
            disabled=self.disable_3d,
        )

    def create_toggle_volume_visibility(self):
        return vuetify.VSwitch(
            label="3D Volume visibility",
            v_model=("volume_visibility", True),
            hide_details=True,
            dense=True,
            solo=True,
        )

    def create_orientation_radio_buttons(self):
        return vuetify.VRadioGroup(
            children=[
                vuetify.VRadio(label="XY", value=f"{SLICE_ORIENTATION_XY}"),
                vuetify.VRadio(label="XZ", value=f"{SLICE_ORIENTATION_XZ}"),
                vuetify.VRadio(label="ZY", value=f"{SLICE_ORIENTATION_YZ}"),
            ],
            v_model=("orientation", f"{SLICE_ORIENTATION_XY}"),
            label="Slice orientation:",
            disabled=self.disable_2d,
        )

    def create_toggle_window_details_button(self):
        return vuetify.VSwitch(
            v_model=("slice_detailed_sliders", False),
            label="Detailed window/level sliders",
            hide_details=True,
            dense=True,
            disabled=self.disable_2d,
            solo=True,
        )

    def create_slice_slider(self):
        return vuetify.VSlider(v_model=("slice", self.default_slice),
                               min=0,
                               max=self.max_slice,
                               step=1,
                               hide_details=True,
                               dense=True,
                               label="Slice",
                               thumb_label=True,
                               disabled=self.disable_2d,
                               style="max-width: 300px")

    def create_toggle_slice_visibility(self):
        return vuetify.VSwitch(label="2D Slice visibility",
                               v_model=("slice_visibility", True),
                               hide_details=True,
                               dense=True,
                               solo=True)

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

    def construct_slice_window_slider(self):
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

        return vuetify.VSlider(v_model=("slice_window", self.slice_window_default),
                               min=min_value,
                               max=max_value,
                               step=step,
                               hide_details=True,
                               disabled=self.disable_2d,
                               dense=True,
                               label="Slice window",
                               thumb_label=True,
                               style=style)

    def construct_slice_level_slider(self):
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

        return vuetify.VSlider(v_model=("slice_level", self.slice_level_default),
                               min=min_value,
                               max=max_value,
                               step=step,
                               hide_details=True,
                               dense=True,
                               disabled=self.disable_2d,
                               label="Slice level",
                               thumb_label=True,
                               style=style)

    def construct_slice_window_range_slider(self):
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
            disabled=self.disable_2d,
            label="Slice window",
            thumb_label=True,
            style=style,
        )

    def construct_color_slider(self):
        if self.cmax > 100:
            # Use actual values
            min_value = self.cmin
            max_value = self.cmax
            step = 1
            self.color_slider_is_percentage = False
        else:
            # Use percentages
            min_value = 0
            max_value = 100
            step = 0.5
            self.color_slider_is_percentage = True

        return vuetify.VRangeSlider(label="Color range",
                                    hide_details=True,
                                    solo=True,
                                    v_model=("coloring", self.windowing_defaults),
                                    min=min_value,
                                    max=max_value,
                                    step=step,
                                    disabled=self.disable_3d,
                                    thumb_label=True,
                                    style="max-width: 300px")

    def construct_windowing_slider(self):
        if self.cmax > 100:
            # Use actual values
            min_value = self.cmin
            max_value = self.cmax
            step = 1
            self.windowing_slider_is_percentage = False
        else:
            # Use percentages
            min_value = 0
            max_value = 100
            step = 0.5
            self.windowing_slider_is_percentage = True

        return vuetify.VRangeSlider(label="Windowing",
                                    hide_details=True,
                                    solo=True,
                                    v_model=("windowing", self.windowing_defaults),
                                    min=min_value,
                                    max=max_value,
                                    step=step,
                                    disabled=self.disable_3d,
                                    thumb_label=True,
                                    style="max-width: 300px")

    def update_windowing_defaults(self, method="scalar"):
        self.cmin, self.cmax = self.cil_viewer.getVolumeMapWindow((0., 100.), method)
        self.windowing_defaults = self.cil_viewer.getVolumeMapWindow((80., 99.), method)
        self.slice_window_range_defaults = self.cil_viewer.getVolumeMapWindow((5., 95.), "scalar")
        self.slice_level_default = self.cil_viewer.getSliceColorLevel()
        self.slice_window_default = self.cil_viewer.getSliceColorWindow()
        if hasattr(self, "windowing_range_slider") and self.windowing_range_slider is not None \
                and hasattr(self, "color_slider") and self.color_slider is not None:
            self.windowing_range_slider = self.construct_windowing_slider()
            self.color_slider = self.construct_color_slider()
            self.slice_window_range_slider = self.construct_slice_window_range_slider()
            self.slice_level_slider = self.construct_slice_level_slider()
            self.slice_window_slider = self.construct_slice_window_slider()
            self.construct_drawer_layout()
            update_layout(self.layout)
        app = vuetify.get_app_instance()
        app.set(key="windowing", value=self.windowing_defaults)
        app.set(key="coloring", value=self.windowing_defaults)

    def update_slice_data(self):
        self.max_slice = self.cil_viewer.img3D.GetExtent()[self.cil_viewer.sliceOrientation * 2 + 1]
        self.default_slice = round(self.max_slice / 2)
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
            update_layout(self.layout)

    def start(self):
        self.layout.start()

    def load_file(self, file_name, windowing_method="scalar", first_load=False):
        if "data" not in file_name:
            file_name = os.path.join("data", file_name)
        if ".nxs" in file_name:
            self.load_nexus_file(file_name)
        else:
            self.load_image(file_name)

        # Update default values
        if not first_load:
            self.update_slice_data()
            self.update_windowing_defaults(windowing_method)
            self.original_cam_data = CameraData(self.cil_viewer.ren.GetActiveCamera())

        # Reset all the buttons and camera
        self.reset_defaults()

    def load_image(self, image_file: str):
        reader = vtkMetaImageReader()
        reader.SetFileName(image_file)
        reader.Update()
        self.cil_viewer.setInput3DData(reader.GetOutput())

    def load_nexus_file(self, file_name):
        reader = cilHDF5ResampleReader()
        reader.SetFileName(file_name)
        reader.SetDatasetName('entry1/tomo_entry/data/data')
        reader.SetTargetSize(256 * 256 * 256)
        reader.Update()
        self.cil_viewer.setInput3DData(reader.GetOutput())

    def switch_render(self):
        self.cil_viewer.style.ToggleVolumeVisibility()
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def switch_slice(self):
        if self.cil_viewer.imageSlice.GetVisibility():
            self.cil_viewer.imageSlice.VisibilityOff()
        else:
            self.cil_viewer.imageSlice.VisibilityOn()
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def switch_to_orientation(self, slice_orientation):
        self.cil_viewer.sliceOrientation = slice_orientation
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def change_color_map(self, cmap):
        self.cil_viewer.setVolumeColorMapName(cmap)
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def set_opacity_mapping(self, opacity):
        self.update_windowing_defaults(opacity)
        self.cil_viewer.setVolumeRenderOpacityMethod(opacity)
        self.html_view.update()

    def change_windowing(self, min_value, max_value, windowing_method="scalar"):
        if self.windowing_slider_is_percentage:
            if windowing_method == "scalar":
                self.cil_viewer.setScalarOpacityPercentiles(min_value, max_value)
            else:
                self.cil_viewer.setGradientOpacityPercentiles(min_value, max_value)
        else:
            if windowing_method == "scalar":
                self.cil_viewer.setScalarOpacityWindow(min_value, max_value)
            else:
                self.cil_viewer.setGradientOpacityWindow(min_value, max_value)
        if hasattr(self, "html_view"):
            self.html_view.update()

    def reset_cam(self):
        self.cil_viewer.adjustCamera(resetcamera=True)
        if hasattr(self, "original_cam_data"):
            self.original_cam_data.copy_data_to_other_camera(self.cil_viewer.ren.GetActiveCamera())
        if hasattr(self, "html_view"):
            self.html_view.update()

    def reset_defaults(self):
        self.set_default_button_state()
        self.reset_cam()

    def set_default_button_state(self):
        # Don't reset file name
        app = vuetify.get_app_instance()
        app.set(key="slice", value=self.default_slice)
        app.set(key="orientation", value=f"{SLICE_ORIENTATION_XY}")
        app.set(key="opacity", value="scalar")
        app.set(key="color_map", value="viridis")
        app.set(key="windowing", value=self.windowing_defaults)
        app.set(key="coloring", value=self.windowing_defaults)
        app.set(key="slice_visibility", value=True)
        app.set(key="volume_visibility", value=True)
        app.set(key="slice_detailed_sliders", value=False)
        app.set(key="slice_window_range", value=self.cil_viewer.getVolumeMapWindow((5., 95.), "scalar"))
        app.set(key="slice_window", value=self.cil_viewer.getSliceColorWindow())
        app.set(key="slice_level", value=self.cil_viewer.getSliceColorLevel())
        app.set(key="background_color", value="cil_viewer_blue")
        app.set(key="toggle_clipping", value=False)
        app.set(key="show_slice_histogram", value=False)
        # Ensure 2D is on
        if not self.cil_viewer.imageSlice.GetVisibility():
            self.switch_slice()
        # Ensure 3D is on
        if not self.cil_viewer.volume.GetVisibility():
            self.switch_render()
        # Reset clipping on the volume itself
        if self.cil_viewer.volume.GetMapper().GetClippingPlanes() is not None:
            self.cil_viewer.volume.GetMapper().RemoveAllClippingPlanes()
        if self.cil_viewer.clipping_plane_initialised:
            self.cil_viewer.style.SetVolumeClipping(False)
            self.remove_clipping_plane()

    def change_coloring(self, min_value, max_value):
        if self.color_slider_is_percentage:
            self.cil_viewer.setVolumeColorPercentiles(min_value, max_value)
        else:
            self.cil_viewer.setVolumeColorWindow(min_value, max_value)
        if hasattr(self, "html_view"):
            self.html_view.update()

    def change_slice_window_range(self, window, level):
        self.cil_viewer.setSliceColorWindowLevel(window, level)

    def change_slice_window(self, new_window):
        self.cil_viewer.setSliceColorWindow(window=new_window)

    def change_slice_level(self, new_level):
        self.cil_viewer.setSliceColorLevel(level=new_level)

    def change_window_level_detail_sliders(self, show_detailed):
        if show_detailed == self.slice_window_sliders_are_detailed:
            return
        # Translate current color level and color window to range_min and range_max
        current_level = self.cil_viewer.getSliceColorLevel()
        current_window = self.cil_viewer.getSliceColorWindow()
        range_min = (current_window - 2 *
                     current_level) / -2  # The reverse of the window calculation in web_app.change_slice_window_level
        range_max = current_window + range_min

        # Setup the defaults pre-flip
        self.slice_window_range_defaults = [range_min, range_max]
        self.slice_level_default = current_level
        self.slice_window_default = current_window

        # Toggle the detailed sliders
        self.slice_window_sliders_are_detailed = show_detailed

        # Reconstruct the detailed sliders
        self.slice_window_range_slider = self.construct_slice_window_range_slider()
        self.slice_window_slider = self.construct_slice_window_slider()
        self.slice_level_slider = self.construct_slice_level_slider()

        # Reconstruct the drawer and push it
        self.construct_drawer_layout()
        update_layout(self.layout)

    def change_slice_visibility(self, visibility):
        if visibility:
            self.cil_viewer.imageSlice.VisibilityOn()
            self.disable_2d = False
        else:
            self.cil_viewer.imageSlice.VisibilityOff()
            self.disable_2d = True
        self.create_drawer_ui_elements()
        update_layout(self.layout)
        self.cil_viewer.updatePipeline()

    def change_volume_visibility(self, visibility):
        if not self.cil_viewer.volume_render_initialised:
            self.cil_viewer.installVolumeRenderActorPipeline()

        if visibility:
            self.disable_3d = False
        else:
            self.disable_3d = True
        self.cil_viewer.style.SetVolumeVisibility(visibility)
        self.create_drawer_ui_elements()
        update_layout(self.layout)
        self.cil_viewer.updatePipeline()

    def change_background_color(self, color):
        if color == "cil_viewer_blue":
            color_data = (.1, .2, .4)
        else:
            color_data = getattr(colors, color.lower())
        self.cil_viewer.ren.SetBackground(color_data)
        self.cil_viewer.updatePipeline()

    def change_clipping(self, clipping_on):
        app = vuetify.get_app_instance()
        if clipping_on:
            app.set(key="slice_visibility", value=False)
        self.cil_viewer.style.SetVolumeClipping(clipping_on)
        self.cil_viewer.updatePipeline()

    def remove_clipping_plane(self):
        if hasattr(self.cil_viewer, "planew"):
            app = vuetify.get_app_instance()
            app.set(key="toggle_clipping", value=False)

            self.cil_viewer.remove_clipping_plane()

            self.cil_viewer.getRenderer().Render()
            self.cil_viewer.updatePipeline()

    def show_slice_histogram(self, show_histogram):
        self.cil_viewer.updateSliceHistogram()
        if show_histogram:
            self.cil_viewer.histogramPlotActor.VisibilityOn()
        else:
            self.cil_viewer.histogramPlotActor.VisibilityOff()
        self.html_view.update()

    def change_slice_number(self, slice_number):
        self.cil_viewer.updateSliceHistogram()
        self.cil_viewer.setActiveSlice(slice_number)
        self.cil_viewer.updatePipeline()
        self.html_view.update()
