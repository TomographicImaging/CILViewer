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
from trame.app import get_server

from ccpi.web_viewer.trame_viewer import TrameViewer

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

from trame.widgets import vuetify

from ccpi.viewer.CILViewer import CILViewer
from ccpi.viewer.CILViewer2D import SLICE_ORIENTATION_XY

server = get_server()
state, ctrl = server.state, server.controller

DEFAULT_SLICE = 32
INITIAL_IMAGE = "head.mha"


class TrameViewer3D(TrameViewer):

    def __init__(self, list_of_files=None):
        super().__init__(list_of_files=list_of_files, viewer=CILViewer)

        # Define attributes that will be constructed in methods outside of __init__

        # omin, omax = min, max for volume opacity - may be scalar or gradient range:
        self.omin = None
        self.omax = None
        # cmin, cmax = min, max for slice and volume colors - scalar range:
        self.cmin = None
        self.cmax = None
        self.windowing_defaults = None
        self.slice_window_range_defaults = None
        self.slice_level_default = None
        self.slice_window_default = None
        self.slice_interaction_col = None
        self.slice_interaction_row = None
        self.slice_interaction_section = None
        self.volume_interaction_col = None
        self.volume_interaction_row = None
        self.volume_interaction_section = None
        self.disable_2d = False
        self.disable_3d = False

        # Define UI elements in __init__ to quiet down Pep8
        self.model_choice = None
        self.background_choice = None
        self.toggle_slice_visibility = None
        self.slice_slider = None
        self.toggle_window_details_button = None
        self.orientation_radio_buttons = None
        self.auto_window_level_button = None
        self.slice_window_range_slider = None
        self.slice_window_slider = None
        self.slice_level_slider = None
        self.show_slice_histogram_switch = None
        self.toggle_volume_visibility = None
        self.opacity_radio_buttons = None
        self.color_choice = None
        self.clipping_switch = None
        self.color_slider = None
        self.windowing_range_slider = None
        self.reset_cam_button = None
        self.reset_defaults_button = None
        self.clipping_removal_button = None

        self.set_opacity_mapping("scalar")

        self.update_slice_slider_data()

        self.create_drawer_ui_elements()

        self.construct_drawer_layout()

        self.layout.content.children = [
            vuetify.VContainer(fluid=True, classes="pa-0 fill-height", children=[self.html_view])
        ]

        # Setup default state
        self.set_default_button_state()

    def construct_drawer_layout(self):
        # The difference is that we use range slider instead of detailed sliders
        self.slice_interaction_col = vuetify.VCol([
            self.toggle_slice_visibility, self.slice_slider, self.orientation_radio_buttons,
            self.auto_window_level_button, self.show_slice_histogram_switch, self.toggle_window_details_button,
            self.slice_window_range_slider, self.slice_window_slider, self.slice_level_slider
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
        self.slice_slider = self.create_slice_slider(disabled=self.disable_2d)
        self.toggle_window_details_button = self.create_toggle_window_details_button(disabled=self.disable_2d)
        self.auto_window_level_button = self.create_auto_window_level_button(disabled=self.disable_2d)
        self.orientation_radio_buttons = self.create_orientation_radio_buttons(disabled=self.disable_2d)
        self.slice_window_range_slider = self.construct_slice_window_range_slider(disabled=self.disable_2d)
        self.slice_window_slider = self.construct_slice_window_slider(disabled=self.disable_2d)
        self.slice_level_slider = self.construct_slice_level_slider(disabled=self.disable_2d)
        self.show_slice_histogram_switch = self.construct_show_slice_histogram_switch(disabled=self.disable_2d)
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

    def create_reset_defaults_button(self):
        return vuetify.VBtn("Reset defaults", hide_details=True, dense=True, solo=True, click=self.reset_defaults)

    def construct_show_slice_histogram_switch(self, disabled: bool):
        return vuetify.VSwitch(
            label="Show slice histogram",
            v_model=("show_slice_histogram", False),
            hide_details=True,
            dense=True,
            solo=True,
            disabled=disabled,
        )

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

    def create_toggle_slice_visibility(self):
        return vuetify.VSwitch(label="2D Slice visibility",
                               v_model=("slice_visibility", True),
                               hide_details=True,
                               dense=True,
                               solo=True)

    def construct_color_slider(self):
        if not self.window_level_sliders_are_percentages:
            # Use actual values
            min_value = self.cmin
            max_value = self.cmax
            step = 1
        else:
            # Use percentages
            min_value = 0
            max_value = 100
            step = 0.5

        v_model = ("coloring", self.coloring_defaults)

        return vuetify.VRangeSlider(label="Color range",
                                    hide_details=True,
                                    solo=True,
                                    v_model=v_model,
                                    min=min_value,
                                    max=max_value,
                                    step=step,
                                    disabled=self.disable_3d,
                                    thumb_label=True,
                                    style="max-width: 300px")

    def construct_windowing_slider(self):
        if not self.window_level_sliders_are_percentages:
            # Use actual values
            min_value = self.omin
            max_value = self.omax
            step = 1
        else:
            # Use percentages
            min_value = 0
            max_value = 100
            step = 0.5

        v_model = ("windowing", self.windowing_defaults)

        return vuetify.VRangeSlider(label="Windowing",
                                    hide_details=True,
                                    solo=True,
                                    v_model=v_model,
                                    min=min_value,
                                    max=max_value,
                                    step=step,
                                    disabled=self.disable_3d,
                                    thumb_label=True,
                                    style="max-width: 300px")

    def update_windowing_defaults(self, method="scalar"):
        self.update_slice_data()
        state["opacity"] = method
        # Set omin and omax after set_slice_defaults because set_slice only uses scalar whereas we need to support gradient in 3D
        # omin, max = min, max for volume opacity - may be scalar or gradient range
        self.omin, self.omax = self.cil_viewer.getImageMapRange((0., 100.), method)
        # cmin, cmax = min, max for slice and volume colors - scalar range
        self.cmin, self.cmax = self.cil_viewer.getImageMapRange((0., 100.), "scalar")

        if hasattr(self, 'window_level_sliders_are_percentages') and self.window_level_sliders_are_percentages:
            self.coloring_defaults = 5., 95.
            self.windowing_defaults = 80., 99.
        else:
            self.windowing_defaults = self.cil_viewer.getImageMapRange((80., 99.), method)
            # colors always set based on scalar mapping:
            self.coloring_defaults = self.cil_viewer.getImageMapRange((5., 95.), "scalar")


        if hasattr(self, "windowing_range_slider") and self.windowing_range_slider is not None \
                and hasattr(self, "color_slider") and self.color_slider is not None:
            self.windowing_range_slider = self.construct_windowing_slider()
            self.color_slider = self.construct_color_slider()
            self.slice_window_range_slider = self.construct_slice_window_range_slider(self.disable_2d)
            self.slice_level_slider = self.construct_slice_level_slider(self.disable_2d)
            self.slice_window_slider = self.construct_slice_window_slider(self.disable_2d)
            self.construct_drawer_layout()
            self.layout.flush_content()

        state["windowing"] = self.windowing_defaults
        state["coloring"] = self.coloring_defaults

    def load_file(self, file_name, windowing_method="scalar"):
        # Perform the load before updating the UI
        super().load_file(file_name, windowing_method=windowing_method)
        # Update default values, there is an assumption this will not be called in the __init__ of this class.
        self.update_slice_slider_data()
        self.update_windowing_defaults(windowing_method)

        # Reset all the buttons and camera
        self.reset_defaults()

    def switch_render(self):
        self.cil_viewer.style.ToggleVolumeVisibility()
        self.cil_viewer.updatePipeline()
        if hasattr(self, 'html_view'):
            self.html_view.update()

    def switch_slice(self):
        if self.cil_viewer.imageSlice.GetVisibility():
            self.cil_viewer.imageSlice.VisibilityOff()
        else:
            self.cil_viewer.imageSlice.VisibilityOn()
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def change_color_map(self, cmap):
        self.cil_viewer.setVolumeColorMapName(cmap)
        self.cil_viewer.updatePipeline()
        self.html_view.update()

    def set_opacity_mapping(self, opacity):
        self.cil_viewer.setVolumeRenderOpacityMethod(opacity)
        self.update_windowing_defaults(opacity)
        self.cil_viewer.updateVolumePipeline()
        self.html_view.update()

    def change_windowing(self, min_value, max_value, windowing_method="scalar"):
        if self.window_level_sliders_are_percentages:
            if windowing_method == "scalar":
                self.cil_viewer.setScalarOpacityPercentiles(min_value, max_value)
            else:
                self.cil_viewer.setGradientOpacityPercentiles(min_value, max_value)
        else:
            if windowing_method == "scalar":
                self.cil_viewer.setScalarOpacityRange(min_value, max_value)
            else:
                self.cil_viewer.setGradientOpacityRange(min_value, max_value)
        if hasattr(self, "html_view"):
            self.html_view.update()

    def reset_cam(self):
        self.cil_viewer.resetCameraToDefault()
        if hasattr(self, "html_view"):
            self.html_view.update()

    def reset_defaults(self):
        self.set_default_button_state()
        self.reset_cam()

    def set_default_button_state(self):
        # Don't reset file name
        state["slice"] = self.default_slice
        state["orientation"] = f"{SLICE_ORIENTATION_XY}"
        state["opacity"] = "scalar"
        state["color_map"] = "viridis"
        # resets to window-level for slice based on 5th, 95th percentiles over volume:
        min, max = self.cil_viewer.getImageMapRange((5., 95.), "scalar")
        window, level = self.cil_viewer.getSliceWindowLevelFromRange(min, max)
        if hasattr(self, 'window_level_sliders_are_percentages') and self.window_level_sliders_are_percentages:
            state["windowing"] = self.windowing_defaults
            state["coloring"] = self.coloring_defaults
            # window level of slice:
            state["slice_window_percentiles"] = (5., 95.)
            state["slice_window_as_percentage"] = self.convert_value_to_percentage(window)
            state["slice_level_as_percentage"] = self.convert_value_to_percentage(level)
        else:
            state["windowing"] = self.windowing_defaults
            state["coloring"] = self.coloring_defaults
            # window level of slice:
            state["slice_window_range"] = (min, max)
            state["slice_window"] = window
            state["slice_level"] = level

        state["slice_visibility"] = True
        state["volume_visibility"] = True
        state["slice_detailed_sliders"] = False
        state["background_color"] = "cil_viewer_blue"
        state["toggle_clipping"] = False
        state["show_slice_histogram"] = False
        # Ensure 2D is on
        if not self.cil_viewer.imageSlice.GetVisibility():
            self.switch_slice()
        # Ensure 3D is on
        if (not self.cil_viewer.volume_render_initialised) or (not self.cil_viewer.volume.GetVisibility()):
            self.switch_render()
        # Reset clipping on the volume itself:
        if self.cil_viewer.volume_render_initialised:
            if self.cil_viewer.volume.GetMapper().GetClippingPlanes() is not None:
                self.cil_viewer.volume.GetMapper().RemoveAllClippingPlanes()
        if self.cil_viewer.clipping_plane_initialised:
            self.cil_viewer.style.SetVolumeClipping(False)
            self.remove_clipping_plane()

    def change_coloring(self, min_value, max_value):
        if self.window_level_sliders_are_percentages:
            self.cil_viewer.setVolumeColorPercentiles(min_value, max_value)
        else:
            self.cil_viewer.setVolumeColorRange(min_value, max_value)
        if hasattr(self, "html_view"):
            self.html_view.update()

    def change_window_level_detail_sliders(self, show_detailed):
        super().change_window_level_detail_sliders(show_detailed)

        # Reconstruct the detailed sliders
        self.slice_window_range_slider = self.construct_slice_window_range_slider(self.disable_2d)
        self.slice_window_slider = self.construct_slice_window_slider(self.disable_2d)
        self.slice_level_slider = self.construct_slice_level_slider(self.disable_2d)

        # Reconstruct the drawer and push it
        self.construct_drawer_layout()
        self.layout.flush_content()

    def change_slice_visibility(self, visibility):
        if visibility:
            self.cil_viewer.imageSlice.VisibilityOn()
            self.disable_2d = False
        else:
            self.cil_viewer.imageSlice.VisibilityOff()
            self.disable_2d = True
            state["show_slice_histogram"] = False
        self.create_drawer_ui_elements()
        self.layout.flush_content()
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
        self.layout.flush_content()
        self.cil_viewer.updatePipeline()

    def change_clipping(self, clipping_on):
        if clipping_on:
            state["slice_visibility"] = False
        self.cil_viewer.style.SetVolumeClipping(clipping_on)
        self.cil_viewer.updatePipeline()

    def remove_clipping_plane(self):
        if hasattr(self.cil_viewer, "planew"):
            state["toggle_clipping"] = False
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
