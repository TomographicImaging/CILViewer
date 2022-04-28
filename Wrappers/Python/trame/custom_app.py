import matplotlib.pyplot as plt
from trame import state
from trame.html import vtk, vuetify
from trame.layouts import FullScreenPage, SinglePageWithDrawer, SinglePage
from vtkmodules.vtkIOImage import vtkMetaImageReader
from vtkmodules.vtkRenderingCore import vtkRenderer, vtkRenderWindow, vtkRenderWindowInteractor

from ccpi.viewer.CILViewer import CILViewer
from ccpi.viewer.CILViewer2D import SLICE_ORIENTATION_XY, SLICE_ORIENTATION_XZ, SLICE_ORIENTATION_YZ

DEFAULT_SLICE = 32
DEFAULT_SLICE_ORIENTATION = SLICE_ORIENTATION_XY
DEFAULT_CONTRAST = 50
DEFAULT_LEVELS = 1
INITIAL_IMAGE = "head.mha"


def load_image(image_file: str):
    reader = vtkMetaImageReader()
    reader.SetFileName(image_file)
    reader.Update()
    return reader.GetOutput()


class TrameViewer:
    def __init__(self):
        self.image = load_image(INITIAL_IMAGE)

        self.cil_viewer = CILViewer()

        # Setup defaults situation
        self.cil_viewer.setInput3DData(self.image)
        self.cil_viewer.setVolumeRenderOpacityMethod('scalar')
        self.cil_viewer.setActiveSlice(DEFAULT_SLICE)
        self.switch_render()

        self.html_view = vtk.VtkRemoteView(
            self.cil_viewer.renWin,
            # interactor_events=("events", 'KeyPress'),
            # KeyPress=(on_key_press, "[$event.keyCode]"),
        )

        self.layout = SinglePageWithDrawer("CILViewer on web", on_ready=self.html_view.update, width=300)
        self.layout.title.set_text("CILViewer on Web")
        self.layout.logo.children = [vuetify.VIcon("mdi-skull", classes="mr-4")]

        self.max_slice = self.cil_viewer.img3D.GetExtent()[self.cil_viewer.sliceOrientation * 2 + 1]

        # replace this with the list browser? # https://kitware.github.io/trame/docs/module-widgets.html#ListBrowser
        self.model_choice = vuetify.VSelect(
            v_model=("file_name", "head.mha"),
            items=("file_name_options", ["head.mha", "FullHead.mhd"]),
            hide_details=True,
            solo=True,
        )

        self.slice_slider = vuetify.VSlider(
            v_model=("slice", DEFAULT_SLICE),
            min=0,
            max=self.max_slice,
            step=1,
            hide_details=True,
            dense=True,
            label="Slice",
            thumb_label=True,
            style="max-width: 300px"
        )

        self.orientation_radio_buttons = vuetify.VRadioGroup(
            children=[
                vuetify.VRadio(label="XY", value=SLICE_ORIENTATION_XY),
                vuetify.VRadio(label="XZ", value=SLICE_ORIENTATION_XZ),
                vuetify.VRadio(label="ZY", value=SLICE_ORIENTATION_YZ),
            ],
            v_model=("orientation", SLICE_ORIENTATION_XY),
            # row=True,
            label="Slice orientation:"
        )

        self.colour_choice = vuetify.VSelect(
            v_model=("colour_map", "viridis"),
            items=("colour_map_options", plt.colormaps()),
            hide_details=True,
            solo=True,
        )

        # Add contrast slider
        self.contrast_slider = vuetify.VSlider(
            v_model=("contrast", DEFAULT_CONTRAST),
            min=0,
            max=100,
            step=1,
            hide_details=True,
            dense=True,
            label="Contrast",
            thumb_label=True,
            style="max-width: 300px"
        )
        # Add levels slider
        self.levels_slider = vuetify.VSlider(
            v_model=("levels", DEFAULT_LEVELS),
            min=0,
            max=100,
            step=1,
            hide_details=True,
            dense=True,
            label="Levels",
            thumb_label=True,
            style="max-width: 300px"
        )

        self.model_3d_button = vuetify.VBtn(
            "Toggle 3D representation",
            hide_details=True,
            dense=True,
            solo=True,
            click=self.switch_render,
        )

        self.slice_button = vuetify.VBtn(
            "Toggle 2D Slice",
            hide_details=True,
            dense=True,
            solo=True,
            click=self.switch_slice,
        )

        # TODO: Add reset defaults

        self.opacity_radio_buttons = vuetify.VRadioGroup(
            children=[
                vuetify.VRadio(label="Scalar", value="scalar"),
                vuetify.VRadio(label="Gradient", value="gradient"),
            ],
            v_model=("opacity", "Scalar"),
            label="Opacity mapping:"
        )

        self.slice_interaction_col = vuetify.VCol([
            self.slice_slider,
            self.orientation_radio_buttons,
            self.slice_button
        ])
        self.slice_interaction_row = vuetify.VRow(self.slice_interaction_col)
        self.slice_interaction_section = vuetify.VContainer(self.slice_interaction_row)

        self.volume_interaction_col = vuetify.VCol([
            self.opacity_radio_buttons,
            self.colour_choice,
            # Clipping button
            # Windowing slider
            self.model_3d_button
        ])
        self.volume_interaction_row = vuetify.VRow(self.volume_interaction_col)
        self.volume_interaction_section = vuetify.VContainer(self.volume_interaction_row)

        self.layout.drawer.children += [
            self.model_choice,
            vuetify.VDivider(),
            self.slice_interaction_section,
            vuetify.VDivider(),
            self.volume_interaction_section,
            vuetify.VDivider(),
            # Select Volume of interest
            # Reset to Defaults
        ]

        self.layout.children += [
            vuetify.VContainer(
                fluid=True,
                classes="pa-0 fill-height",
                children=[self.html_view],
            )
        ]

    def start(self):
        self.layout.start()

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

    def switch_slice(self):
        if self.cil_viewer.imageSlice.GetVisibility():
            self.cil_viewer.imageSlice.VisibilityOff()
        else:
            self.cil_viewer.imageSlice.VisibilityOn()
        self.cil_viewer.updatePipeline()

    def switch_to_orientation(self, slice_orientation):
        self.cil_viewer.sliceOrientation = slice_orientation
        self.cil_viewer.updatePipeline()

    def change_colour_map(self, cmap):
        self.cil_viewer.setVolumeColorMapName(cmap)
        self.cil_viewer.updatePipeline()

    def set_opacity_mapping(self, opacity):
        self.cil_viewer.setVolumeRenderOpacityMethod(opacity)
        self.cil_viewer.installVolumeRenderActorPipeline()


TRAME_VIEWER = TrameViewer()


@state.change("slice")
def update_slice(**kwargs):
    TRAME_VIEWER.cil_viewer.setActiveSlice(kwargs["slice"])
    TRAME_VIEWER.cil_viewer.updatePipeline()


@state.change("contrast")
def update_contrast(**kwargs):
    # TRAME_VIEWER.cil_viewer
    pass


@state.change("orientation")
def change_orientation(**kwargs):
    if "orientation" in kwargs:
        orientation = kwargs["orientation"]
        TRAME_VIEWER.switch_to_orientation(int(orientation))


@state.change("opacity")
def change_opacity_mapping(**kwargs):
    if "opacity" in kwargs:
        TRAME_VIEWER.set_opacity_mapping(kwargs["opacity"])


@state.change("file_name")
def change_model(_):
    # TODO: Implement change the model and slice being displayed in the viewer to the new file
    pass


@state.change("colour_map")
def change_colour_map(**kwargs):
    TRAME_VIEWER.change_colour_map(kwargs['colour_map'])


if __name__ == "__main__":
    TRAME_VIEWER.start()
