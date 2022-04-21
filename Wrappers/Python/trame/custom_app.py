from trame.html import vtk, vuetify
from trame.layouts import FullScreenPage
from vtkmodules.vtkIOImage import vtkMetaImageReader
from vtkmodules.vtkRenderingCore import vtkRenderer, vtkRenderWindow, vtkRenderWindowInteractor

from ccpi.viewer.CILViewer import CILViewer


def switch_render(cil_viewer):
    # Switch to the 3D render
    if not cil_viewer.volume_render_initialised:
        cil_viewer.installVolumeRenderActorPipeline()

    if cil_viewer.volume.GetVisibility():
        cil_viewer.volume.VisibilityOff()
        cil_viewer.light.SwitchOff()
    else:
        cil_viewer.volume.VisibilityOn()
        cil_viewer.light.SwitchOn()
    cil_viewer.updatePipeline()


def switch_off_slice(cil_viewer):
    if cil_viewer.imageSlice.GetVisibility():
        cil_viewer.imageSlice.VisibilityOff()
    else:
        cil_viewer.imageSlice.VisibilityOn()
    cil_viewer.updatePipeline()


def start_cilviewer():
    renderer = vtkRenderer()
    renderWindow = vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    renderWindowInteractor = vtkRenderWindowInteractor()

    reader = vtkMetaImageReader()
    reader.SetFileName("head.mha")
    reader.Update()
    image = reader.GetOutput()

    cil_viewer = CILViewer(ren=renderer, renWin=renderWindow, iren=renderWindowInteractor)
    cil_viewer.setInput3DData(image)
    cil_viewer.setVolumeRenderOpacityMethod('scalar')
    switch_render(cil_viewer)
    # switch_off_slice(cil_viewer)

    html_view = vtk.VtkRemoteView(renderWindow)

    layout = FullScreenPage("CILViewer on web", on_ready=html_view.update)

    layout.children += [
        vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
            children=[html_view],
        )
    ]

    layout.start()


if __name__ == "__main__":
    start_cilviewer()
