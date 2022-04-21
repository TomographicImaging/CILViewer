from trame.layouts import SinglePage, FullScreenPage
from trame.html import vtk, vuetify

from vtkmodules.vtkFiltersSources import vtkConeSource
from vtkmodules.vtkIOImage import vtkMetaImageReader
from vtkmodules.vtkImagingCore import vtkExtractVOI
from vtkmodules.vtkImagingStatistics import vtkImageHistogramStatistics
from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor, vtkImageSlice, vtkImageSliceMapper,
)

# Required for interactor initialization
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa

# Required for rendering initialization, not necessary for
# local rendering, but doesn't hurt to include it
import vtkmodules.vtkRenderingOpenGL2  # noqa


# -----------------------------------------------------------------------------
# VTK pipeline
# -----------------------------------------------------------------------------

renderer = vtkRenderer()
renderWindow = vtkRenderWindow()
renderWindow.AddRenderer(renderer)

iren = vtkRenderWindowInteractor()
iren.SetRenderWindow(renderWindow)
iren.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

# Add the orientation marker
om = vtkAxesActor()
ori = vtkOrientationMarkerWidget()
ori.SetOutlineColor(0.9300, 0.5700, 0.1300)
ori.SetInteractor(iren)
ori.SetOrientationMarker(om)
ori.SetViewport(0.0, 0.0, 0.4, 0.4)
ori.SetEnabled(1)
ori.InteractiveOff()

reader = vtkMetaImageReader()
reader.SetFileName('head.mha')
reader.Update()

voi = vtkExtractVOI()
voi.SetInputData(reader.GetOutput())

imageSlice = vtkImageSlice()
imageSliceMapper = vtkImageSliceMapper()
imageSlice.SetMapper(imageSliceMapper)
imageSlice.GetProperty().SetInterpolationTypeToNearest()

num_slice = 32

extent = list(reader.GetOutput().GetExtent())
extent[4] = num_slice
extent[5] = num_slice + 1
voi.SetVOI(extent)

imageSliceMapper.SetInputConnection(voi.GetOutputPort())

ia = vtkImageHistogramStatistics()
ia.SetInputConnection(voi.GetOutputPort())
ia.SetAutoRangePercentiles(5.0, 95.)
ia.Update()
cmin, cmax = ia.GetAutoRange()
level = (cmin + cmax) / 2
window = (cmax - cmin) / 2
imageSlice.GetProperty().SetColorLevel(level)
imageSlice.GetProperty().SetColorWindow(window)

renderer.AddActor(imageSlice)
renderer.ResetCamera()

# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------

html_view = vtk.VtkRemoteView(renderWindow)

layout = FullScreenPage("Hello trame", on_ready=html_view.update)
# layout.title.set_text("Hello trame")

layout.children += [
    vuetify.VContainer(
        fluid=True,
        classes="pa-0 fill-height",
        children=[html_view],
    )
]

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    layout.start()
