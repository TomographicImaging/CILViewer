from ccpi.viewer import viewer2D
from ccpi.viewer.utils.conversion import cilHDF5ResampleReader, cilNumpyResampleReader
from ccpi.viewer.utils.colormaps import CILColorMaps
import vtk
import os, sys
from functools import partial



def display(viewer, reader, input=0):
    if input == 0:
        viewer.setInputData(reader.GetOutput())
    else:
        viewer.setInputData2(reader.GetOutput())
def report (*args, **kwargs):
    print ("###################### REPORT #########################")
    print (args)
    for k,v in kwargs.items():
        print (k, v)

############### Handle events
def OnMouseWheelForward(self, interactor_style, event):
    interactor = interactor_style.GetInteractor()
    current_slice = self.GetSlice()
    # smin = self.GetSliceMin()
    smax = self.GetSliceMax()
    if current_slice < smax:
        advance = 1
        if interactor.GetShiftKey():
            advance = 10
        self.SetSlice(current_slice + advance)
        v.cornerAnnotation.SetText(0, 'slice {}/{}'.format(self.GetSlice(), smax))
        OnMouseMove(self, interactor, event)
    return 1

def OnMouseWheelBackward(self, interactor_style, event):
    interactor = interactor_style.GetInteractor()
    current_slice = self.GetSlice()
    smin = self.GetSliceMin()
    smax = self.GetSliceMax()
    if current_slice > smin:
        advance = 1
        if interactor.GetShiftKey():
            advance = 10
        self.SetSlice(current_slice - advance)
        self.cornerAnnotation.SetText(0, 'slice {}/{}'.format(self.GetSlice(), smax))
        OnMouseMove(self, interactor, event)
    return 1

def OnMouseMove(self, interactor_style, event):
    self.cornerAnnotation.SetText(1, 'Level {}\nWindow {}'.format(self.GetColorLevel(), self.GetColorWindow()))
    self.cornerAnnotation.SetText(3, '{}'.format(self.GetImageActor()))
    if hasattr(self, 'imageTracer'):
        self.cornerAnnotation.SetText(2, 'Tracer Enabled {}'.format(self.imageTracer.GetEnabled()))
        if self.imageTracer.GetEnabled():
            pass
    return 0
    

def OnKeyPress(self, interactor_style, event):
    interactor = interactor_style.GetInteractor()
    spacing = self.GetInput().GetSpacing()
    we = self.GetImageActor().GetDisplayExtent()
    bounds = [spacing[0] * we[0], spacing[0] * we[1] , 
        spacing[1] * we[2], spacing[1] * we[3],
        spacing[2] * we[4], spacing[2] * we[5] ]
    if interactor.GetKeyCode() == "x":
        self.SetSliceOrientationToYZ()
        if hasattr(self, 'imageTracer'):
            self.imageTracer.SetProjectionNormalToXAxes()        
            bounds[0] = self.GetImageActor().GetSliceNumber() * spacing[0]
            bounds[1] = self.GetImageActor().GetSliceNumber() * spacing[0]
            self.imageTracer.SetProjectionPosition(bounds[0])
    elif interactor.GetKeyCode() == "y":
        self.SetSliceOrientationToXZ()
        if hasattr(self, 'imageTracer'):
            self.imageTracer.SetProjectionNormalToYAxes()
            bounds[2] = self.GetImageActor().GetSliceNumber() * spacing[1]
            bounds[3] = self.GetImageActor().GetSliceNumber() * spacing[1]
            self.imageTracer.SetProjectionPosition(bounds[2])
    elif interactor.GetKeyCode() == "z":
        self.SetSliceOrientationToXY()
        if hasattr(self, 'imageTracer'):
            self.imageTracer.SetProjectionNormalToZAxes()
            bounds[4] = self.GetImageActor().GetSliceNumber() * spacing[2]
            bounds[5] = self.GetImageActor().GetSliceNumber() * spacing[2]
            self.imageTracer.SetProjectionPosition(bounds[4])
    elif interactor.GetKeyCode() == "t":
        if not hasattr( self, 'imageTracer'):
            v = self
            # ImageTracer
            v.imageTracer = vtk.vtkImageTracerWidget()
            self.imageTracer.SetViewProp(self.GetImageActor())
            # self.imageTracer.SetInputData(self.GetInput())
            # set Interactor
            v.imageTracer.SetInteractor(interactor)
            v.imageTracer.SetCaptureRadius(1.5)
            # v.imageTracer.GetLineProperty().SetColor(0.8, 0.8, 1.0)
            v.imageTracer.GetLineProperty().SetLineWidth(3.0)
            v.imageTracer.GetHandleProperty().SetColor(0.4, 0.4, 1.0)
            # v.imageTracer.GetSelectedHandleProperty().SetColor(1.0, 1.0, 1.0)
            # Set the size of the glyph handle
            v.imageTracer.GetGlyphSource().SetScale(10.0)
            # Set the initial rotation of the glyph if desired.  The default glyph
            # set internally by the widget is a '+' so rotating 45 deg. gives a 'x'
            v.imageTracer.GetGlyphSource().SetRotationAngle(45.0)
            v.imageTracer.GetGlyphSource().Modified()
            v.imageTracer.ProjectToPlaneOn()

            # v.imageTracer.SnapToImageOn()
            # v.imageTracer.SetHandleRightMouseButton(True)
            # Set autoclose to on
            # v.imageTracer.AutoCloseOn()
            # v.imageTracer.SetProjectionNormal(2)
            # v.imageTracer.SetProjectionPosition(0)
            self.imageTracer.SetEnabled(False)
            # self.imageTracer.On()
            # self.imageTracer.InteractionOn()
            
            
        if (self.imageTracer.GetEnabled()):
            self.imageTracer.SetEnabled(False)
            self.imageTracer.InteractionOff()
            self.imageTracer.HandleLeftMouseButtonOff()
            self.imageTracer.Off()
        else:
            self.imageTracer.SetEnabled(True)
            self.imageTracer.InteractionOn()
            self.imageTracer.HandleLeftMouseButtonOn()
            self.imageTracer.On()
        self.cornerAnnotation.SetText(2, 'Tracer Enabled {}'.format(self.imageTracer.GetEnabled()))

def OnLeftButtonClick(self, style, event):
    if hasattr( self, 'imageTracer'):
        if self.imageTracer.GetEnabled():
            self.cornerAnnotation.SetText(2, 'button click Tracer Enabled {}'.format(self.imageTracer.GetEnabled()))
        else:
            style.OnLeftButtonDown()
    else:
        style.OnLeftButtonDown()

if __name__=='__main__':
    # fpath = 'C:/Users/ofn77899/Data/LizardHead/astra'
    # reader = cilHDF5ResampleReader()
    # # reader.SetFileName("C:/Users/ofn77899/Data/CTMeeting2022/PDHG_iTV_alpha_0.0005_it_1000.nxs")
    # reader.SetFileName(os.path.join(fpath, "lizard_TVTGV_ch_59.nxs"))
    # reader.SetDatasetName('entry1/tomo_entry/data/data')
    # #reader.AddObserver(vtk.vtkCommand.ProgressEvent, progress)
    # # reader.Update()


    # # reader = vtk.vtkMetaImageReader()
    # # reader.SetFileName('head.mha')
    # # reader.Update()

    # reader2 = cilHDF5ResampleReader()
    # reader2.SetFileName(os.path.join(fpath, "lizard_TVTGV_ch_55.nxs"))
    # # reader2.SetFileName("C:/Users/ofn77899/Data/CTMeeting2022/PDHG_iTV_alpha_0.001_it_1000.nxs")
    # reader2.SetDatasetName('entry1/tomo_entry/data/data')

    # reader2.SetFileName(os.path.join(os.path.abspath('C:/Users/ofn77899/Data/CTMeeting2022'), 'small_normSPDHG_eTV_alpha_0.0003_it_210.nxs'))
    # # # reader.ReadDataSetInfo()
    # reader2.Update()

    # #calculate reader2 output scalar range
    # stats = vtk.vtkImageHistogramStatistics()
    # stats.SetInputConnection(reader2.GetOutputPort())
    # stats.Update()

    reader = vtk.vtkMetaImageReader()
    reader.SetFileName('head.mha')
    reader.Update()

    
    # reader2 = cilNumpyResampleReader()
    # reader2.SetFileName(os.path.abspath('C:/Users/ofn77899/Data/dvc/frame_000_f.npy'))
    # reader2.SetTargetSize(1024**3)
    # reader2.Update()
    # print (reader2.GetOutput().GetDimensions())

    use_vtk = False if sys.argv[1] == 'cil' else True
    if use_vtk:

        
        v = vtk.vtkImageViewer2()   
        # v = vtk.vtkResliceImageViewer()
        iren = vtk.vtkRenderWindowInteractor()
        
        v.GetRenderWindow().SetInteractor(iren)
        v.GetRenderWindow().SetSize(600,600)
        v.SetInputData(reader.GetOutput())
        v.SetColorLevel(800)
        v.SetColorWindow(899)
        v.SetSlice(42)
        v.SetupInteractor(iren)
        # v.GetRenderer().SetBackground(.1, .2, .4)
        v.GetInteractorStyle().SetInteractionModeToImageSlicing()

        # corner annotation
        v.cornerAnnotation = vtk.vtkCornerAnnotation()
        v.cornerAnnotation.SetMaximumFontSize(12)
        v.cornerAnnotation.PickableOff()
        v.cornerAnnotation.VisibilityOn()
        v.cornerAnnotation.GetTextProperty().ShadowOn()
        v.cornerAnnotation.SetLayerNumber(1)
        v.GetRenderer().AddViewProp(v.cornerAnnotation)

        # axis orientation widget
        om = vtk.vtkAxesActor()
        ori = vtk.vtkOrientationMarkerWidget()
        ori.SetOutlineColor(0.9300, 0.5700, 0.1300)
        ori.SetInteractor(iren)
        ori.SetOrientationMarker(om)
        ori.SetViewport(0.0, 0.0, 0.2, 0.2)
        ori.SetEnabled(1)
        ori.InteractiveOff()

        # # cursor doesn't show up
        # v.cursor = vtk.vtkCursor2D()
        # v.cursorMapper = vtk.vtkPolyDataMapper2D()
        # v.cursorActor = vtk.vtkActor2D()
        # v.cursor.SetModelBounds(-10, 10, -10, 10, 0, 0)
        # v.cursor.SetFocalPoint(0, 0, 0)
        # v.cursor.AllOff()
        # v.cursor.AxesOn()
        # v.cursorActor.PickableOff()
        # v.cursorActor.VisibilityOn()
        # v.cursorActor.GetProperty().SetColor(1, 1, 1)
        # v.cursorActor.SetLayerNumber(1)
        # v.cursorMapper.SetInputData(v.cursor.GetOutput())
        # v.cursorActor.SetMapper(v.cursorMapper)
        # v.GetRenderer().AddActor(v.cursorActor)

        

        style = v.GetInteractorStyle()
        pOnMouseWheelForward = partial(OnMouseWheelForward, v)
        pOnMouseWheelBackward = partial(OnMouseWheelBackward, v)
        priority = 1

        pOnKeyPress = partial(OnKeyPress, v)
        pOnLeftButtonClick = partial(OnLeftButtonClick, v)
        style.AddObserver("MouseWheelForwardEvent", pOnMouseWheelForward, priority)
        style.AddObserver("MouseWheelBackwardEvent", pOnMouseWheelBackward, priority)
        style.AddObserver('KeyPressEvent', pOnKeyPress, 1.0)
        style.AddObserver('LeftButtonPressEvent', pOnLeftButtonClick, 1.0)
        # pOnMouseMove = partial(OnMouseMove, v)
        # style.AddObserver("MouseMoveEvent", pOnMouseMove, priority/2)

        # print (type(A))
        # iren = v.GetRenderWindow().GetInteractor()
        # v.GetImageActor().SetOpacity(0.2)
        iren.Initialize()
        iren.Start()
        

    else:
        v = viewer2D()

        reader.AddObserver(vtk.vtkCommand.ErrorEvent, report)
        reader2.AddObserver(vtk.vtkCommand.ErrorEvent, report)
        
        # v.setInputData(reader.GetOutput())
        v.setInputData(reader2.GetOutput())



        # transfer_function = CILColorMaps.get_color_transfer_function('viridis', (stats.GetMinimum(), stats.GetMaximum()) )
        # v.lut2 = transfer_function
        # v.image2map.SetLookupTable(transfer_function)
        # v.image2map.Update()
        # v.imageSlice2.Update()

        v.startRenderLoop()