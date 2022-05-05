import os
from dataclasses import dataclass

import matplotlib.pyplot as plt
from trame import state
from trame.html import vtk, vuetify
from trame.layouts import SinglePageWithDrawer
from vtkmodules.vtkIOImage import vtkMetaImageReader
from vtkmodules.vtkRenderingCore import vtkCamera

from ccpi.viewer.CILViewer import CILViewer
from ccpi.viewer.CILViewer2D import SLICE_ORIENTATION_XY, SLICE_ORIENTATION_XZ, SLICE_ORIENTATION_YZ
from ccpi.viewer.utils.conversion import cilHDF5ResampleReader

DEFAULT_SLICE = 32
INITIAL_IMAGE = "head.mha"


@dataclass(init=False)
class CameraData:
    position: list
    focalPoint: list
    viewUp: list

    def __init__(self, camera: vtkCamera):
        self.position = camera.GetPosition()
        self.focalPoint = camera.GetFocalPoint()
        self.viewUp = camera.GetViewUp()

    def copy_data_to_other_camera(self, other_cam: vtkCamera):
        other_cam.SetPosition(*self.position)
        other_cam.SetFocalPoint(*self.focalPoint)
        other_cam.SetViewUp(*self.viewUp)


class TrameViewer:
    def __init__(self):
        self.cmax = None
        self.cmin = None
        self.windowing_defaults = None
        self.max_slice = None
        self.default_slice = None
        self.image = None

        self.cil_viewer = CILViewer()
        self.load_file(INITIAL_IMAGE)

        self.html_view = vtk.VtkRemoteView(
            self.cil_viewer.renWin,
            # interactor_events=("events", 'KeyPress'),
            # KeyPress=(on_key_press, "[$event.keyCode]"),
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
            v_model=("file_name", "head.mha"),
            items=("file_name_options", ["head.mha", "egg2.nxs", "fbp_reconstruction_mouse_512.nxs",
                                         "small_normSPDHG_eTV_alpha_0.0003_it_1260.nxs", "walnut_recon.nxs"]),
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

        self.slice_button = vuetify.VBtn(
            "Toggle 2D Slice",
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

        self.windowing_slider = vuetify.VRangeSlider(
            label="Windowing range",
            hide_details=True,
            solo=True,
            v_model=("windowing", self.windowing_defaults),
            min=self.cmin,
            max=self.cmax,
            step=1,
            thumb_label=True,
            style="max-width: 300px"
        )

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
            self.clipping_button,
            self.windowing_slider,
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
            vuetify.VDivider(),
            self.reset_cam_button,
            vuetify.VDivider(),
            self.reset_defaults_button
        ]

        self.layout.children += [
            vuetify.VContainer(
                fluid=True,
                classes="pa-0 fill-height",
                children=[self.html_view],
            )
        ]

        # Setup default state
        self.set_default_button_state()

    def update_windowing_defaults(self):
        self.cil_viewer.ia.SetAutoRangePercentiles(0., 100.)  # Used to grab the min and max defaults using CILViewer.ia
        self.cil_viewer.ia.Update()
        self.cmin, self.cmax = self.cil_viewer.ia.GetAutoRange()
        self.cil_viewer.ia.SetAutoRangePercentiles(80., 99.)  # Used in the default of CILViewer.getColorOpacityForVolumeRender
        self.cil_viewer.ia.Update()
        if hasattr(self.cil_viewer, "volume_colormap_limits"):
            self.windowing_defaults = [self.cil_viewer.volume_colormap_limits[0], self.cil_viewer.volume_colormap_limits[1]]

    def update_slice_data(self):
        self.max_slice = self.cil_viewer.img3D.GetExtent()[self.cil_viewer.sliceOrientation * 2 + 1]
        self.default_slice = round(self.max_slice / 2)

    def start(self):
        self.layout.start()

    def load_file(self, file_name):
        if "data" not in file_name:
            file_name = os.path.join("data", file_name)
        if ".nxs" in file_name:
            self.load_nexus_file(file_name)
        else:
            self.load_image(file_name)

        # Update default values
        self.update_windowing_defaults()
        self.update_slice_data()

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
        reader.SetTargetSize(1024 * 1024 * 1024)
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
        self.cil_viewer.setVolumeRenderOpacityMethod(opacity)
        self.html_view.update()

    def change_windowing(self, min_value, max_value):
        self.cil_viewer.setVolumeColorLevelWindow(min_value, max_value)
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


TRAME_VIEWER = TrameViewer()


@state.change("slice")
def update_slice(**kwargs):
    TRAME_VIEWER.cil_viewer.setActiveSlice(kwargs["slice"])
    TRAME_VIEWER.cil_viewer.updatePipeline()
    TRAME_VIEWER.html_view.update()


@state.change("orientation")
def change_orientation(**kwargs):
    if "orientation" in kwargs:
        orientation = kwargs["orientation"]
        if orientation is not int:
            orientation = int(orientation)
        TRAME_VIEWER.switch_to_orientation(int(orientation))


@state.change("opacity")
def change_opacity_mapping(**kwargs):
    if "opacity" in kwargs:
        TRAME_VIEWER.set_opacity_mapping(kwargs["opacity"])


@state.change("file_name")
def change_model(**kwargs):
    TRAME_VIEWER.load_file(kwargs['file_name'])


@state.change("colour_map")
def change_colour_map(**kwargs):
    TRAME_VIEWER.change_colour_map(kwargs['colour_map'])


@state.change("windowing")
def change_windowing(**kwargs):
    TRAME_VIEWER.change_windowing(min_value=kwargs["windowing"][0], max_value=kwargs["windowing"][1])


if __name__ == "__main__":
    TRAME_VIEWER.start()
