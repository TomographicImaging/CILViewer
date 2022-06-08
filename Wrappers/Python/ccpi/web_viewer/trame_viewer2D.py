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
from trame import update_layout
from trame.html import vuetify

from ccpi.viewer.CILViewer2D import CILViewer2D
from ccpi.web_viewer.trame_viewer import TrameViewer


class TrameViewer2D(TrameViewer):
    def __init__(self, list_of_files: list = None):
        super().__init__(list_of_files=list_of_files, viewer_class=CILViewer2D)

        self.model_choice = None
        self.background_choice = None
        self.slice_slider = None
        self.orientation_radio_buttons = None
        self.auto_window_level_button = None
        self.toggle_window_details_button = None
        self.slice_window_range_slider = None
        self.slice_window_slider = None
        self.slice_level_slider = None
        self.tracing_switch = None
        self.line_profile_switch = None
        self.interpolation_of_slice_switch = None
        self.reset_defaults_button = None
        self.slice_interaction_col = None
        self.slice_interaction_row = None
        self.slice_interaction_section = None

        self.create_drawer_ui_elements()

        self.construct_drawer_layout()

        self.layout.children += [
            vuetify.VContainer(
                fluid=True,
                classes="pa-0 fill-height",
                children=[self.html_view],
            )
        ]

    def create_drawer_ui_elements(self):
        self.model_choice = self.create_model_selector()
        self.background_choice = self.create_background_selector()
        self.slice_slider = self.create_slice_slider()
        self.orientation_radio_buttons = self.create_orientation_radio_buttons()
        self.toggle_window_details_button = self.create_toggle_window_details_button()
        self.auto_window_level_button = self.create_auto_window_level_button()
        self.slice_window_range_slider = self.construct_slice_window_range_slider()
        self.slice_window_slider = self.construct_slice_window_slider()
        self.slice_level_slider = self.construct_slice_level_slider()
        self.tracing_switch = self.create_tracing_switch()
        # self.line_profile_switch = self.create_line_profile_switch()
        self.interpolation_of_slice_switch = self.create_interpolation_of_slice_switch()
        self.reset_defaults_button = self.create_reset_defaults_button()

    def construct_drawer_layout(self):
        # The difference is that we use range slider instead of detailed sliders
        self.slice_interaction_col = vuetify.VCol([
            self.slice_slider,
            self.orientation_radio_buttons,
            self.auto_window_level_button,
            self.toggle_window_details_button,
            self.slice_window_range_slider,
            self.slice_window_slider,
            self.slice_level_slider,
            self.tracing_switch,
            self.interpolation_of_slice_switch
        ])
        self.slice_interaction_row = vuetify.VRow(self.slice_interaction_col)
        self.slice_interaction_section = vuetify.VContainer(self.slice_interaction_row)
        self.layout.drawer.children = [
            "Choose model to load",
            self.model_choice,
            vuetify.VDivider(),
            "Choose background color",
            self.background_choice,
            vuetify.VDivider(),
            self.slice_interaction_section,
            vuetify.VDivider(),
            self.reset_defaults_button
        ]

    def create_auto_window_level_button(self):
        return vuetify.VBtn(
            "Auto Window/Level",
            hide_details=True,
            dense=True,
            solo=True,
            click=self.auto_window_level
        )

    def create_tracing_switch(self):
        return vuetify.VSwitch(
            label="Toggle Tracing",
            v_model=("toggle_tracing", False),
            hide_details=True,
            dense=True,
            solo=True
        )

    # def create_line_profile_switch(self):
    #     return vuetify.VSwitch(
    #         label="Toggle Line Profiling",
    #         v_model=("toggle_profiling", False),
    #         hide_details=True,
    #         dense=True,
    #         solo=True,
    #     )

    def create_interpolation_of_slice_switch(self):
        return vuetify.VSwitch(
            label="Toggle Interpolation",
            v_model=("toggle_interpolation", False),
            hide_details=True,
            dense=True,
            solo=True,
        )

    def create_reset_defaults_button(self):
        return vuetify.VBtn(
            "Reset Defaults",
            hide_details=True,
            dense=True,
            solo=True,
            click=self.reset_defaults
        )

    def change_tracing(self, tracing: bool):
        if tracing:
            self.cil_viewer.imageTracer.On()
        else:
            self.cil_viewer.imageTracer.Off()

    # def change_profiling(self, profiling: bool):
    #     if not profiling:
    #         self.SetEventInactive("SHOW_LINE_PROFILE_EVENT")
    #         self.DisplayLineProfile(interactor, event, False)
    #     else:
    #         self.SetEventActive("SHOW_LINE_PROFILE_EVENT")
    #         self.DisplayLineProfile(interactor, event, True)

    def change_interpolation(self, interpolation: bool):
        if not interpolation:
            self.cil_viewer.imageSlice.GetProperty().SetInterpolationTypeToNearest()
        else:
            self.cil_viewer.imageSlice.GetProperty().SetInterpolationTypeToLinear()
        self.cil_viewer.updatePipeline()

    def auto_window_level(self):
        cmin, cmax = self.cil_viewer.ia.GetAutoRange()
        level = (cmin + cmax) / 2
        window = (cmax - cmin) / 2
        app = vuetify.get_app_instance()
        app.set(key="slice_window_range", value=(window, level))
        app.set(key="slice_window", value=window)
        app.set(key="slice_level", value=level)
        self.cil_viewer.updatePipeline()

    def change_window_level_detail_sliders(self, show_detailed: bool):
        super().change_window_level_detail_sliders(show_detailed)

        # Reconstruct the detailed sliders
        self.slice_window_range_slider = self.construct_slice_window_range_slider()
        self.slice_window_slider = self.construct_slice_window_slider()
        self.slice_level_slider = self.construct_slice_level_slider()

        # Reconstruct the drawer and push it
        self.construct_drawer_layout()
        update_layout(self.layout)

    def reset_defaults(self):
        pass
