#
#   Author 2022 Samuel Jones
#   Copyright 2022 SCD Rutherford Appleton Laboratory UKRI
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

import matplotlib.pyplot as plt
from trame import update_layout
from trame.html import vtk, vuetify
from trame.layouts import SinglePageWithDrawer
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
        self.image = None
        self.slice_interaction_col = None
        self.slice_interaction_row = None
        self.slice_interaction_section = None
        self.volume_interaction_col = None
        self.volume_interaction_row = None
        self.volume_interaction_section = None
        self.windowing_slider_is_percentage = False  # Defaults to not percentage with the head.mha file
        self.colour_slider_is_percentage = False  # Defaults to not percentage with the head.mha file
        self.slice_level_slider_is_percentage = False  # Defaults to not percentage with the head.mha file
        self.slice_window_slider_is_percentage = False  # Defaults to not percentage with the head.mha file
        self.slice_window_sliders_are_detailed = False  # Defaults to none-detailed sliders

        if list_of_files is None:
            list_of_files = os.listdir("data/")
        if "head.mha" in list_of_files:
            default_file = "head.mha"
        else:
            default_file = list_of_files[0]

        self.cil_viewer = CILViewer()
        self.load_file(default_file)

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

        # replace this with the list browser? # https://kitware.github.io/trame/docs/module-widgets.html#ListBrowser
        self.model_choice = vuetify.VSelect(
            v_model=("file_name", default_file),
            items=("file_name_options", list_of_files),
            hide_details=True,
            solo=True,
        )

        self.slice_slider = vuetify.VSlider(
            v_model=("slice", self.default_slice),
            min=0,
            max=self.max_slice,
            step=1,
            hide_details=True,
            dense=True,
            label="Slice",
            thumb_label=True,
            style="max-width: 300px"
        )

        self.toggle_window_details_button = vuetify.VSwitch(
            v_model=("slice_detailed_sliders", False),
            label="Detailed window/level sliders",
            hide_details=True,
            dense=True,
            solo=True,
        )

        self.slice_window_range_slider = self.construct_slice_window_range_slider()

        self.slice_window_slider = self.construct_slice_window_slider()
        self.slice_level_slider = self.construct_slice_level_slider()

        self.orientation_radio_buttons = vuetify.VRadioGroup(
            children=[
                vuetify.VRadio(label="XY", value=f"{SLICE_ORIENTATION_XY}"),
                vuetify.VRadio(label="XZ", value=f"{SLICE_ORIENTATION_XZ}"),
                vuetify.VRadio(label="ZY", value=f"{SLICE_ORIENTATION_YZ}"),
            ],
            v_model=("orientation", f"{SLICE_ORIENTATION_XY}"),
            label="Slice orientation:"
        )

        self.opacity_radio_buttons = vuetify.VRadioGroup(
            children=[
                vuetify.VRadio(ref="opacity_scalar_button", label="Scalar", value="scalar"),
                vuetify.VRadio(label="Gradient", value="gradient"),
            ],
            v_model=("opacity", "scalar"),
            label="Opacity mapping:"
        )

        self.colour_choice = vuetify.VSelect(
            v_model=("colour_map", "viridis"),
            items=("colour_map_options", plt.colormaps()),
            hide_details=True,
            solo=True,
        )

        self.model_3d_button = vuetify.VBtn(
            "Toggle 3D representation",
            hide_details=True,
            dense=True,
            solo=True,
            click=self.cil_viewer.style.ToggleVolumeVisibility,
        )

        self.slice_button = vuetify.VSwitch(
            label="2D Slice visibility",
            hide_details=True,
            dense=True,
            solo=True,
            click=self.cil_viewer.style.ToggleSliceVisibility,
        )

        self.clipping_button = vuetify.VBtn(
            "Toggle Clipping",
            hide_details=True,
            dense=True,
            solo=True,
            click=self.cil_viewer.style.ToggleVolumeClipping,
        )

        self.update_windowing_defaults()
        self.colour_slider = self.construct_colour_slider()
        self.windowing_range_slider = self.construct_windowing_slider()

        self.reset_cam_button = vuetify.VBtn(
            "Reset Camera",
            hide_details=True,
            dense=True,
            solo=True,
            click=self.reset_cam,
        )

        self.reset_defaults_button = vuetify.VBtn(
            "Reset defaults",
            hide_details=True,
            dense=True,
            solo=True,
            click=self.reset_defaults
        )

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

    def on_key_press(self, key):
        pass

    def construct_drawer_layout(self):
        # The difference is that we use range slider instead of detailed sliders
        self.slice_interaction_col = vuetify.VCol([
            self.slice_button,
            self.slice_slider,
            self.orientation_radio_buttons,
            self.toggle_window_details_button,
            self.slice_window_range_slider,
            self.slice_window_slider,
            self.slice_level_slider
        ])
        self.slice_interaction_row = vuetify.VRow(self.slice_interaction_col)
        self.slice_interaction_section = vuetify.VContainer(self.slice_interaction_row)

        self.volume_interaction_col = vuetify.VCol([
            self.opacity_radio_buttons,
            self.colour_choice,
            self.colour_slider,
            self.clipping_button,
            self.windowing_range_slider,
            self.model_3d_button
        ])
        self.volume_interaction_row = vuetify.VRow(self.volume_interaction_col)
        self.volume_interaction_section = vuetify.VContainer(self.volume_interaction_row)

        self.layout.drawer.children = [
            self.model_choice,
            vuetify.VDivider(),
            self.slice_interaction_section,
            vuetify.VDivider(),
            self.volume_interaction_section,
            vuetify.VDivider(),
            # Select Volume of interest
            vuetify.VDivider(),
            self.reset_cam_button,
            vuetify.VDivider(),
            self.reset_defaults_button
        ]

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

        return vuetify.VSlider(
            v_model=("slice_window", self.slice_window_default),
            min=min_value,
            max=max_value,
            step=step,
            hide_details=True,
            dense=True,
            label="Slice window",
            thumb_label=True,
            style=style
        )

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

        return vuetify.VSlider(
            v_model=("slice_level", self.slice_level_default),
            min=min_value,
            max=max_value,
            step=step,
            hide_details=True,
            dense=True,
            label="Slice level",
            thumb_label=True,
            style=style
        )

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
            label="Slice window",
            thumb_label=True,
            style=style,
        )

    def construct_colour_slider(self):
        if self.cmax > 100:
            # Use actual values
            min_value = self.cmin
            max_value = self.cmax
            step = 1
            self.colour_slider_is_percentage = False
        else:
            # Use percentages
            min_value = 0
            max_value = 100
            step = 0.5
            self.colour_slider_is_percentage = True
        
        return vuetify.VRangeSlider(
            label="Colour range",
            hide_details=True,
            solo=True,
            v_model=("colouring", self.windowing_defaults),
            min=min_value,
            max=max_value,
            step=step,
            thumb_label=True,
            style="max-width: 300px"
        )

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

        return vuetify.VRangeSlider(
            label="Windowing",
            hide_details=True,
            solo=True,
            v_model=("windowing", self.windowing_defaults),
            min=min_value,
            max=max_value,
            step=step,
            thumb_label=True,
            style="max-width: 300px"
        )

    def update_windowing_defaults(self, method="scalar"):
        self.cmin, self.cmax = self.cil_viewer.getVolumeMapWindow((0., 100.), method)
        self.windowing_defaults = self.cil_viewer.getVolumeMapWindow((80., 99.), method)
        self.slice_window_range_defaults = self.cil_viewer.getVolumeMapWindow((5., 95.), "scalar")
        self.slice_level_default = self.cil_viewer.getSliceColourLevel()
        self.slice_window_default = self.cil_viewer.getSliceColourWindow()
        if hasattr(self, "windowing_range_slider") and hasattr(self, "colour_slider"):
            self.windowing_range_slider = self.construct_windowing_slider()
            self.colour_slider = self.construct_colour_slider()
            self.slice_window_range_slider = self.construct_slice_window_range_slider()
            self.slice_level_slider = self.construct_slice_level_slider()
            self.slice_window_slider = self.construct_slice_window_slider()
            self.construct_drawer_layout()
            update_layout(self.layout)
        app = vuetify.get_app_instance()
        app.set(key="windowing", value=self.windowing_defaults)
        app.set(key="colouring", value=self.windowing_defaults)

    def update_slice_data(self):
        self.max_slice = self.cil_viewer.img3D.GetExtent()[self.cil_viewer.sliceOrientation * 2 + 1]
        self.default_slice = round(self.max_slice / 2)
        if hasattr(self, "slice_slider"):
            self.slice_slider = vuetify.VSlider(
                v_model=("slice", self.default_slice),
                min=0,
                max=self.max_slice,
                step=1,
                hide_details=True,
                dense=True,
                label="Slice",
                thumb_label=True,
                style="max-width: 300px"
            )
            self.construct_drawer_layout()
            update_layout(self.layout)

    def start(self):
        self.layout.start()

    def load_file(self, file_name, windowing_method="scalar"):
        if "data" not in file_name:
            file_name = os.path.join("data", file_name)
        if ".nxs" in file_name:
            self.load_nexus_file(file_name)
        else:
            self.load_image(file_name)

        # Update default values
        self.update_slice_data()
        self.update_windowing_defaults(windowing_method)
        self.original_cam_data = CameraData(self.cil_viewer.ren.GetActiveCamera())

        # Reset all the buttons and camera
        self.reset_defaults()

    def load_image(self, image_file: str):
        reader = vtkMetaImageReader()
        reader.SetFileName(image_file)
        reader.Update()
        self.image = reader.GetOutput()
        self.cil_viewer.setInput3DData(self.image)

    def load_nexus_file(self, file_name):
        reader = cilHDF5ResampleReader()
        reader.SetFileName(file_name)
        reader.SetDatasetName('entry1/tomo_entry/data/data')
        reader.SetTargetSize(256 * 256 * 256)
        reader.Update()
        self.image = reader.GetOutput()
        self.cil_viewer.setInput3DData(self.image)

    def switch_render(self):
        if not self.cil_viewer.volume_render_initialised:
            self.cil_viewer.installVolumeRenderActorPipeline()

        if self.cil_viewer.volume.GetVisibility():
            self.cil_viewer.volume.VisibilityOff()
            self.cil_viewer.light.SwitchOff()
        else:
            self.cil_viewer.volume.VisibilityOn()
            self.cil_viewer.light.SwitchOn()
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

    def change_colour_map(self, cmap):
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
        app.set(key="colour_map", value="viridis")
        app.set(key="windowing", value=self.windowing_defaults)
        app.set(key="colouring", value=self.windowing_defaults)
        app.set(key="slice_window_range", value=self.cil_viewer.getVolumeMapWindow((5., 95.), "scalar"))
        # Ensure 2D is on
        if not self.cil_viewer.imageSlice.GetVisibility():
            self.switch_slice()
        # Ensure 3D is on
        if not self.cil_viewer.volume.GetVisibility():
            self.switch_render()
        # Reset clipping on the volume itself
        if self.cil_viewer.volume.GetMapper().GetClippingPlanes() is not None:
            self.cil_viewer.volume.GetMapper().RemoveAllClippingPlanes()
        if hasattr(self.cil_viewer, 'planew'):
            self.cil_viewer.style.ToggleVolumeClipping()
            
    def change_slice_window_range(self, window, level):
        self.cil_viewer.setSliceColourWindowLevel(window, level)

    def change_slice_window(self, new_window):
        self.cil_viewer.setSliceColourWindow(window=new_window)

    def change_slice_level(self, new_level):
        self.cil_viewer.setSliceColourLevel(level=new_level)

    def change_window_level_detail_sliders(self, show_detailed):
        if show_detailed == self.slice_window_sliders_are_detailed:
            return
        # Translate current colour level and colour window to range_min and range_max
        current_level = self.cil_viewer.getSliceColourLevel()
        current_window = self.cil_viewer.getSliceColourWindow()
        range_min = (current_window - 2 * current_level) / -2  # The reverse of the window calculation in web_app.change_slice_window_level
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
