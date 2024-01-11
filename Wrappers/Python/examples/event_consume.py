import vtk
import logging

logging.basicConfig(level=logging.DEBUG)



def updateCameraPosition(ren, interactor, event):
    logging.info(f"updateCameraPosition: {interactor.GetKeyCode()}")
    if interactor.GetKeyCode() == "c":
        logging.info("camera position {}".format(ren.GetActiveCamera().GetPosition()))
        logging.info("camera distance {}".format(ren.GetActiveCamera().GetDistance()))
        logging.info("camera focal point {}".format(ren.GetActiveCamera().GetFocalPoint()))
        logging.info("camera view up {}".format(ren.GetActiveCamera().GetViewUp()))
        logging.info("camera Roll {}".format(ren.GetActiveCamera().GetRoll()))
    elif interactor.GetKeyCode() == "w":
        logging.info(f"updateCameraPosition: {interactor.GetKeyCode()}")

def consumeKeyPress(ren, interactor, event):
    # https://vtk.org/pipermail/vtk-developers/2007-September/020213.html
    # https://vtk.org/Wiki/VTK/Python_Wrapper_Enhancement#Wrap_vtkCommand_and_allow_it_to_be_subclassed
    logging.info(f"consumeKeyPress: {interactor.GetKeyCode()}")
    if interactor.GetKeyCode() in ["s", "w"]:
        logging.info("consuming keypress {}".format(interactor.GetKeyCode()))
        interactor.SetKeyCode("")
    

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



# cube source
cube = vtk.vtkCubeSource()
cube.SetXLength(4)
cube.SetYLength(3)
cube.SetZLength(2)

sphere = vtk.vtkSphereSource()
sphere.SetRadius(1)

shape = cube

shape.Update()

actor = vtk.vtkLODActor()

lw = 10.0
actor.GetProperty().SetColor(1,0,0)
actor.GetProperty().SetOpacity(0.5)
actor.GetProperty().SetLineWidth(lw)
actor.GetProperty().SetRepresentationToWireframe()
actor.GetProperty().SetRenderLinesAsTubes(True)
logging.info("representation {}".format(actor.GetProperty().GetRepresentationAsString()))
logging.info("render lines as tubes {}".format(actor.GetProperty().GetRenderLinesAsTubes()))

mapper = vtk.vtkPolyDataMapper()
actor.SetMapper(mapper)

mapper.SetInputData(shape.GetOutput())
mapper.Update()

ren.AddActor(actor)


from functools import partial
onUpdateCameraPosition = partial(updateCameraPosition, ren)
iren.AddObserver("KeyPressEvent", onUpdateCameraPosition, 1.0)
iren.AddObserver("KeyPressEvent", partial(consumeKeyPress, ren), 20)

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

camera = vtk.vtkCamera()

camera.SetPosition(0, 0, 1)
camera.Elevation(180)

ren.SetActiveCamera(camera)
ren.ResetCamera()

iren.Start()
