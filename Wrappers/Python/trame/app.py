# Needs to install trame, vtk, h5py

from trame.layouts import FullScreenPage
from trame.html import vtk, vuetify

# VTK imports
from vtkmodules.vtkFiltersSources import vtkConeSource
from vtkmodules.vtkIOImage import vtkMetaImageReader
from vtkmodules.vtkImagingCore import vtkExtractVOI
from vtkmodules.vtkImagingStatistics import vtkImageHistogramStatistics
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor, vtkImageMapper, vtkActor2D, vtkImageSlice, vtkImageSliceMapper,
)
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch, vtkInteractorStyleImage
import vtkmodules.vtkRenderingOpenGL2

from ccpi.viewer.CILViewer2D import CILViewer2D, CILInteractorStyle
from ccpi.viewer.CILViewer import CILViewer


def start_cone_viewer():
    renderer = vtkRenderer()
    renderWindow = vtkRenderWindow()
    renderWindow.AddRenderer(renderer)

    renderWindowInteractor = vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)
    renderWindowInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

    cone_source = vtkConeSource()
    mapper = vtkPolyDataMapper()
    mapper.SetInputConnection(cone_source.GetOutputPort())
    actor = vtkActor()
    actor.SetMapper(mapper)

    renderer.AddActor(actor)
    renderer.ResetCamera()

    html_view = vtk.VtkLocalView(renderWindow)

    layout = FullScreenPage("CILViewer on web", on_ready=html_view.update)
    # layout.title.set_text("CILViewer on Web")

    layout.children += [
        vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
            children=[html_view],
        )
    ]

    layout.start()


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
    html_view = vtk.VtkRemoteView(renderWindow, interactor_events=("events", 'KeyPress'), KeyPress=cil_viewer.style.OnKeyPress)

    layout = FullScreenPage("CILViewer on web", on_ready=html_view.update)

    layout.children += [
        vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
            children=[html_view],
        )
    ]

    layout.start()


def start_viewer_with_cil_interactor_style():
    reader = vtkMetaImageReader()
    reader.SetFileName("head.mha")
    reader.Update()

    mapper = vtkImageMapper()
    mapper.SetInputData(reader.GetOutput())
    actor = vtkActor()
    actor.SetMapper(mapper)

    ren = vtkRenderer()
    ren.AddActor(actor)
    # ren.SetBackground(0.1, 0.2, 0.4)

    renWin = vtkRenderWindow()
    renWin.AddRenderer(ren)
    # renWin.SetSize(400, 400)

    style = CILInteractorStyle(None)
    style.debug = True

    iren = vtkRenderWindowInteractor()
    iren.SetInteractorStyle(style)
    iren.SetRenderWindow(renWin)

    html_view = vtk.VtkLocalView(renWin)

    layout = FullScreenPage("CILViewer on web", on_ready=html_view.update)

    layout.children += [
        vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
            children=[html_view],
        )
    ]

    layout.start()


def start_viewer_edo_pipeline():
    # Essential objects
    ren = vtkRenderer()
    iren = vtkRenderWindowInteractor()
    renWin = vtkRenderWindow()

    # Style of interaction handling
    style = vtkInteractorStyleImage()
    iren.SetInteractorStyle(style)

    # change the background to the signature blue!
    ren.SetBackground(.1, .2, .4)

    # link the basic objects
    iren.SetRenderWindow(renWin)
    renWin.AddRenderer(ren)
    # iren.Initialize()

    # Start pipeline
    # read a dataset
    reader = vtkMetaImageReader()
    reader.SetFileName('head.mha')
    reader.Update()

    # we want a 2D image, we need a VOI, i.e. volume of interest
    voi = vtkExtractVOI()
    # pass the data from the reader
    voi.SetInputData(reader.GetOutput())

    # we need an object to visualise, an Actor or better an vtkImageSlice
    imageSlice = vtkImageSlice()
    # how does it appear? Requires a mapper
    imageSliceMapper = vtkImageSliceMapper()
    imageSlice.SetMapper(imageSliceMapper)
    imageSlice.GetProperty().SetInterpolationTypeToNearest()

    # Which slice do we want?
    num_slice = 32

    # tell the voi which is the extent we are interested in
    extent = list(reader.GetOutput().GetExtent())
    extent[4] = num_slice
    extent[5] = num_slice + 1
    voi.SetVOI(extent)

    # connect the mapper with the data
    imageSliceMapper.SetInputConnection(voi.GetOutputPort())

    # let's set the image level/window, i.e. how much of the slice histogram do we want to accomodate
    ia = vtkImageHistogramStatistics()
    ia.SetInputConnection(voi.GetOutputPort())
    # we want all the values above 5th percentiles, up to 95th. Basically remove outliers and zeros
    ia.SetAutoRangePercentiles(5.0, 95.)
    ia.Update()
    cmin, cmax = ia.GetAutoRange()
    # set the level to the average between the percentiles
    level = (cmin + cmax) / 2
    # accomodates all values between the level an the percentiles
    window = (cmax - cmin) / 2
    imageSlice.GetProperty().SetColorLevel(level)
    imageSlice.GetProperty().SetColorWindow(window)

    # Finally put something (the imageSlice) in the scene to be displayed
    ren.AddActor(imageSlice)

    # start the interactor loop
    # iren.Start()

    html_view = vtk.VtkRemoteView(renWin)

    layout = FullScreenPage("CILViewer on web", on_ready=html_view.update)

    layout.children += [
        vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
            children=[html_view],
        )
    ]

    layout.start()


def start_layout_local():


if __name__ == "__main__":
    # start_cone_viewer()
    # start_cilviewer()
    # start_viewer_with_cil_interactor_style()
    # start_viewer_edo_pipeline()
