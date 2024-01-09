import vtk
import logging

logging.basicConfig(level=logging.DEBUG)

def world2display(coord, spac, orig, renderer):
    # Convert image coordinates to world coordinates
    world_coord = [spac[i] * (coord[i] - orig[i]) for i in range(3)]

    vc = vtk.vtkCoordinate()
    vc.SetCoordinateSystemToWorld()
    vc.SetValue(world_coord)

    return vc.GetComputedDoubleViewportValue(renderer)

def display2world(coord, spac, orig, renderer):
    vc = vtk.vtkCoordinate()
    vc.SetCoordinateSystemToDisplay()
    vc.SetValue(coord[0], coord[1], coord[2])

    world_coord = vc.GetComputedWorldValue(renderer)

    # Convert world coordinates to image coordinates
    image_coord = [(world_coord[i] / spac[i]) + orig[i] for i in range(3)]

    return image_coord

def updateCameraPosition(ren, interactor, event):
    if interactor.GetKeyCode() == "c":
        logging.info("camera position {}".format(ren.GetActiveCamera().GetPosition()))
        logging.info("camera distance {}".format(ren.GetActiveCamera().GetDistance()))
        logging.info("camera focal point {}".format(ren.GetActiveCamera().GetFocalPoint()))
        logging.info("camera view up {}".format(ren.GetActiveCamera().GetViewUp()))
        logging.info("camera Roll {}".format(ren.GetActiveCamera().GetRoll()))


# viewer
renWin = vtk.vtkRenderWindow()
dimX, dimY = 600, 600
renWin.SetSize(dimX, dimY)

iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

# style = vtk.vtkInteractorStyleImage()
style = vtk.vtkInteractorStyleTrackballCamera()
iren.SetInteractorStyle(style)

ren = vtk.vtkRenderer()
ren.SetBackground(.1, .2, .4)
renWin.AddRenderer(ren)

# orientation marker
# axis orientation widget
om = vtk.vtkAxesActor()
ori = vtk.vtkOrientationMarkerWidget()
ori.SetOutlineColor(0.9300, 0.5700, 0.1300)
ori.SetInteractor(iren)
ori.SetOrientationMarker(om)
ori.SetViewport(0.0, 0.0, 0.4, 0.4)
ori.SetEnabled(1)
ori.InteractiveOff()

# DATA DISPLAY

# ImageSlice
# download the image from https://github.com/TomographicImaging/CIL-Data/raw/main/head.mha
# or from VTKData https://github.com/open-cv/VTKData/tree/master/Data/headsq
reader = vtk.vtkMetaImageReader()
reader.SetFileName("head.mha")
reader.Update()

voi = vtk.vtkExtractVOI()
voi.SetInputConnection(reader.GetOutputPort())
extent = reader.GetOutput().GetExtent()
spacing = reader.GetOutput().GetSpacing()
h = (extent[5] + extent[4]) // 2
logging.info("extent {}".format(extent))
logging.info("h {}".format(h))
logging.info("spacing {}".format(reader.GetOutput().GetSpacing()))
logging.info("origin {}".format(reader.GetOutput().GetOrigin()))

voi.SetVOI(extent[0], extent[1], extent[2], extent[3], h, h+1)
voi.Update()

imageSlice = vtk.vtkImageSlice()
ismapper = vtk.vtkImageSliceMapper()
imageSlice.SetMapper(ismapper)
ismapper.SetInputConnection(voi.GetOutputPort())
imageSlice.Update()


# cube source
cube = vtk.vtkCubeSource()
cube.SetXLength(40)
cube.SetYLength(30)
cube.SetZLength(20)

sphere = vtk.vtkSphereSource()
sphere.SetRadius(10)

shape = cube

centre = [0, 0, 0]
for i in range(3):
    centre[i] = (extent[2*i+1] + extent[2*i]) / 2.0 * spacing[i] + reader.GetOutput().GetOrigin()[i]

logging.info("centre {}".format(centre))
shape.SetCenter(*centre)
shape.Update()

actor = vtk.vtkLODActor()

lw = 10.0
actor.GetProperty().SetColor(0.,0,0)
actor.GetProperty().SetEdgeColor(0,0,0)
actor.GetProperty().SetOpacity(0.5)
actor.GetProperty().SetLineWidth(lw)
actor.GetProperty().SetEdgeVisibility(True)
actor.GetProperty().SetEdgeColor(1, 0, 0)

mapper = vtk.vtkPolyDataMapper()
actor.SetMapper(mapper)

# plane clipper
visPlane = [vtk.vtkPlane(), vtk.vtkPlane()]
planeClipper = [vtk.vtkClipPolyData(), vtk.vtkClipPolyData()]
planeClipper[1].SetInputConnection(planeClipper[0].GetOutputPort())

planeClipper[0].SetClipFunction(visPlane[0])
planeClipper[1].SetClipFunction(visPlane[1])

planeClipper[0].InsideOutOn()
planeClipper[1].InsideOutOn()

planeClipper[0].SetInputData(shape.GetOutput())


lw_world = display2world([0,0,lw], spacing, reader.GetOutput().GetOrigin(), ren)
logging.info("lw_world {}".format(lw_world))

# delta = lw_world[2] 
delta = spacing[2]
planeOriginAbove = [centre[0], centre[1], centre[2] + delta]
planeNormalAbove = [0, 0, 1]
planeOriginBelow = [centre[0], centre[1], centre[2] - delta]
planeNormalBelow = [-1 * el for el in planeNormalAbove]

visPlane[0].SetOrigin(*planeOriginAbove)
visPlane[0].SetNormal(*planeNormalAbove)

visPlane[1].SetOrigin(*planeOriginBelow)
visPlane[1].SetNormal(*planeNormalBelow)

planeClipper[0].Update()

planeClipper[1].Update()

mapper.SetInputData(planeClipper[1].GetOutput())
# mapper.SetInputData(shape.GetOutput())
mapper.Update()

ren.AddActor(actor)



ren.AddActor(imageSlice)

camera = ren.GetActiveCamera()

camera = vtk.vtkCamera()
camera.ParallelProjectionOn()
camera.SetFocalPoint(*centre)
# newpos = [339.3854529034713, 81.19176978455286, 561.2842587656584]
# camera.SetPosition(*newpos)
camera.SetPosition(centre[0],centre[1], 1)
camera.Elevation(180)

ren.SetActiveCamera(camera)
ren.ResetCamera()

from functools import partial
onUpdateCameraPosition = partial(updateCameraPosition, ren)
iren.AddObserver("KeyPressEvent", onUpdateCameraPosition)


# add text with vtk version
textProperty = vtk.vtkTextProperty()
textProperty.SetFontSize(20)
textProperty.SetJustificationToCentered()
textProperty.SetColor(0,1,1)

textMapper = vtk.vtkTextMapper()
textMapper.SetInput(vtk.vtkVersion.GetVTKVersion())
textMapper.SetTextProperty(textProperty)

textActor = vtk.vtkActor2D()
textActor.SetMapper(textMapper)
textActor.SetPosition(dimX//2, 20)

ren.AddActor(textActor)

iren.Start()