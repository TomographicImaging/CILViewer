# -*- coding: utf-8 -*-
#   Copyright 2017 Edoardo Pasca
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
   
import vtk
import numpy
#import math
from vtk.util import numpy_support
from enum import Enum

SLICE_ORIENTATION_XY = 2 # Z
SLICE_ORIENTATION_XZ = 1 # Y
SLICE_ORIENTATION_YZ = 0 # X

CONTROL_KEY = 8
SHIFT_KEY = 4
ALT_KEY = -128

class ViewerEvent(Enum):
    # left button
    PICK_EVENT = 0 
    # alt  + right button + move
    WINDOW_LEVEL_EVENT = 1
    # shift + right button
    ZOOM_EVENT = 2
    # control + right button
    PAN_EVENT = 3
    # control + left button
    CREATE_ROI_EVENT = 4
    # alt + left button
    DELETE_ROI_EVENT = 5
    # release button
    NO_EVENT = -1

class CILInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    
    
    
    
    def __init__(self, callback):
        vtk.vtkInteractorStyleTrackballCamera.__init__(self)
        self.callback = callback
        self.RemoveObservers("MouseWheelForwardEvent")
        self.RemoveObservers("MouseWheelBackwardEvent")
        self.RemoveObservers("KeyPressEvent")
        self.RemoveObservers("LeftButtonPressEvent")
        self.RemoveObservers("RightButtonPressEvent")
        self.RemoveObservers("LeftButtonReleaseEvent")
        self.RemoveObservers("RightButtonReleaseEvent")
        self.RemoveObservers("MouseMoveEvent")
        
        priority = 1.0
        
        self.AddObserver("MouseWheelForwardEvent" , callback.OnMouseWheelForward , priority)
        self.AddObserver("MouseWheelBackwardEvent" , callback.OnMouseWheelBackward, priority)
        self.AddObserver('KeyPressEvent', callback.OnKeyPress, priority)
        self.AddObserver('LeftButtonPressEvent', callback.OnLeftButtonPressEvent, priority)
        self.AddObserver('RightButtonPressEvent', callback.OnRightButtonPressEvent, priority)
        self.AddObserver('LeftButtonReleaseEvent', callback.OnLeftButtonReleaseEvent, priority)
        self.AddObserver('RightButtonReleaseEvent', callback.OnRightButtonReleaseEvent, priority)
        self.AddObserver('MouseMoveEvent', callback.OnMouseMoveEvent, priority)
        
        self.InitialEventPosition = (0,0)
        
        
    def SetInitialEventPosition(self, xy):
        self.InitialEventPosition = xy
        
    def GetInitialEventPosition(self):
        return self.InitialEventPosition
    
    def GetKeyCode(self):
        return self.GetInteractor().GetKeyCode()
    
    def SetKeyCode(self, keycode):
        self.GetInteractor().SetKeyCode(keycode)
        
    def GetControlKey(self):
        return self.GetInteractor().GetControlKey() == CONTROL_KEY
    
    def GetShiftKey(self):
        return self.GetInteractor().GetShiftKey() == SHIFT_KEY
    
    def GetAltKey(self):
        return self.GetInteractor().GetAltKey() == ALT_KEY
    
    def GetEventPosition(self):
        return self.GetInteractor().GetEventPosition()
    
    def GetEventPositionInWorldCoordinates(self):
        pass
    
    def GetDeltaEventPosition(self):
        x,y = self.GetInteractor().GetEventPosition()
        return (x - self.InitialEventPosition[0] , y - self.InitialEventPosition[1])
    
    def Dolly(self, factor):
        self.callback.ren.GetActiveCamera().Dolly(factor)
        self.callback.ren.ResetCameraClippingRange()
        

class CILViewer2D():
    '''Simple Interactive Viewer based on VTK classes'''
    
    def __init__(self, dimx=600,dimy=600):
        '''creates the rendering pipeline'''
        # create a rendering window and renderer
        self.ren = vtk.vtkRenderer()
        self.renWin = vtk.vtkRenderWindow()
        self.renWin.SetSize(dimx,dimy)
        self.renWin.AddRenderer(self.ren)
        self.style = CILInteractorStyle(self)
        #self.style = vtk.vtkInteractorStyleTrackballCamera()
        #self.style.SetCallback(self)
        self.iren = vtk.vtkRenderWindowInteractor()
        self.iren.SetInteractorStyle(self.style)
        self.iren.SetRenderWindow(self.renWin)
        self.iren.Initialize()
        self.ren.SetBackground(.1, .2, .4)
        
        self.ren.GetActiveCamera().ParallelProjectionOn()
        
        # data
        self.img3D = None
        self.sliceno = 0
        self.sliceOrientation = SLICE_ORIENTATION_XY
        self.sliceActor = vtk.vtkImageActor()
        self.voi = vtk.vtkExtractVOI()
        self.wl = vtk.vtkImageMapToWindowLevelColors()
        self.ia = vtk.vtkImageAccumulate()
        self.sliceActorNo = 0
        
        self.InitialLevel = 0
        self.InitialWindow = 0
        
        self.event = ViewerEvent.NO_EVENT
        
        # ROI Widget
        self.ROIWidget = vtk.vtkBorderWidget()
        self.ROIWidget.SetInteractor(self.iren)
        self.ROIWidget.CreateDefaultRepresentation()
        self.ROIWidget.GetBorderRepresentation().GetBorderProperty().SetColor(0,1,0)
        self.ROIWidget.AddObserver(vtk.vtkWidgetEvent.Select, self.OnROIModifiedEvent, 1.0)
        
        # edge points of the ROI
        self.ROI = ()
        
        #picker
        self.picker = vtk.vtkPropPicker()
        self.picker.PickFromListOn()
        self.picker.AddPickList(self.sliceActor)

        self.iren.SetPicker(self.picker)
        
        # corner annotation
        self.cornerAnnotation = vtk.vtkCornerAnnotation()
        self.cornerAnnotation.SetMaximumFontSize(12);
        self.cornerAnnotation.PickableOff();
        self.cornerAnnotation.VisibilityOff();
        self.cornerAnnotation.GetTextProperty().ShadowOn();
        self.cornerAnnotation.SetLayerNumber(1);
        
        self.ren.AddViewProp(self.cornerAnnotation)
        
        
        # cursor doesn't show up
        self.cursor = vtk.vtkCursor2D()
        self.cursorMapper = vtk.vtkPolyDataMapper2D()
        self.cursorActor = vtk.vtkActor2D()
        self.cursor.SetModelBounds(-10, 10, -10, 10, 0, 0)
        self.cursor.SetFocalPoint(0, 0, 0)
        self.cursor.AllOff()
        self.cursor.AxesOn()
        self.cursorActor.PickableOff()
        self.cursorActor.VisibilityOn()
        self.cursorActor.GetProperty().SetColor(1, 1, 1)
        self.cursorActor.SetLayerNumber(1)
        self.cursorMapper.SetInputData(self.cursor.GetOutput())
        self.cursorActor.SetMapper(self.cursorMapper)
        
        
        
        
    def GetInteractor(self):
        return self.iren
    
    def GetRenderer(self):
        return self.ren
        
    def setInput3DData(self, imageData):
        self.img3D = imageData
        self.installPipeline()

    def setInputAsNumpy(self, numpyarray):
        if (len(numpy.shape(numpyarray)) == 3):
            doubleImg = vtk.vtkImageData()
            shape = numpy.shape(numpyarray)
            doubleImg.SetDimensions(shape[0], shape[1], shape[2])
            doubleImg.SetOrigin(0,0,0)
            doubleImg.SetSpacing(1,1,1)
            doubleImg.SetExtent(0, shape[0]-1, 0, shape[1]-1, 0, shape[2]-1)
            #self.img3D.SetScalarType(vtk.VTK_UNSIGNED_SHORT, vtk.vtkInformation())
            doubleImg.AllocateScalars(vtk.VTK_DOUBLE,1)
            
            for i in range(shape[0]):
                for j in range(shape[1]):
                    for k in range(shape[2]):
                        doubleImg.SetScalarComponentFromDouble(
                            i,j,k,0, numpyarray[i][j][k])
        #self.setInput3DData( numpy_support.numpy_to_vtk(numpyarray) )
            # rescale to appropriate VTK_UNSIGNED_SHORT
            stats = vtk.vtkImageAccumulate()
            stats.SetInputData(doubleImg)
            stats.Update()
            iMin = stats.GetMin()[0]
            iMax = stats.GetMax()[0]
            scale = vtk.VTK_UNSIGNED_SHORT_MAX / (iMax - iMin)

            shiftScaler = vtk.vtkImageShiftScale ()
            shiftScaler.SetInputData(doubleImg)
            shiftScaler.SetScale(scale)
            shiftScaler.SetShift(iMin)
            shiftScaler.SetOutputScalarType(vtk.VTK_UNSIGNED_SHORT)
            shiftScaler.Update()
            self.img3D = shiftScaler.GetOutput()
            
            self.installPipeline()
    
    def displaySlice(self, sliceno = 0):
        self.sliceno = sliceno
        
        self.updatePipeline()
        
        self.renWin.Render()
        
        return self.sliceActorNo

    def updatePipeline(self):
        extent = [ i for i in self.img3D.GetExtent()]
        extent[self.sliceOrientation * 2] = self.sliceno
        extent[self.sliceOrientation * 2 + 1] = self.sliceno 
        self.voi.SetVOI(extent[0], extent[1],
                   extent[2], extent[3],
                   extent[4], extent[5])
        
        self.voi.Update()
        self.ia.Update()
        self.wl.Update()
        self.sliceActor.SetDisplayExtent(extent[0], extent[1],
                   extent[2], extent[3],
                   extent[4], extent[5])
        self.sliceActor.Update()
        
        self.updateCornerAnnotation("Slice %d/%d" % (self.sliceno + 1 , self.img3D.GetDimensions()[self.sliceOrientation]))
        self.AdjustCamera()
        
        self.renWin.Render()
        
        
    def installPipeline(self):
        '''Slices a 3D volume and then creates an actor to be rendered'''
        self.voi.SetInputData(self.img3D)
        #select one slice in Z
        extent = [ i for i in self.img3D.GetExtent()]
        extent[self.sliceOrientation * 2] = self.sliceno
        extent[self.sliceOrientation * 2 + 1] = self.sliceno 
        self.voi.SetVOI(extent[0], extent[1],
                   extent[2], extent[3],
                   extent[4], extent[5])
        
        self.voi.Update()
        # set window/level for current slices
         
    
        self.wl = vtk.vtkImageMapToWindowLevelColors()
        self.ia.SetInputData(self.voi.GetOutput())
        self.ia.Update()
        cmax = self.ia.GetMax()[0]
        cmin = self.ia.GetMin()[0]
        
        self.InitialLevel = (cmax+cmin)/2
        self.InitialWindow = cmax-cmin

        
        self.wl.SetLevel(self.InitialLevel)
        self.wl.SetWindow(self.InitialWindow)
        
        self.wl.SetInputData(self.voi.GetOutput())
        self.wl.Update()
            
        self.sliceActor.SetInputData(self.wl.GetOutput())
        self.sliceActor.SetDisplayExtent(extent[0], extent[1],
                   extent[2], extent[3],
                   extent[4], extent[5])
        self.sliceActor.Update()
        self.ren.AddActor(self.sliceActor)
        self.AdjustCamera()
        
        self.ren.AddViewProp(self.cursorActor)
        self.cursorActor.VisibilityOn()
        
        self.iren.Initialize()
        self.renWin.Render()
        self.iren.Start()
    
    def AdjustCamera(self):
        self.ren.ResetCamera()
            
    def getROI(self):
        return self.ROI
        
    ############### Handle events
    def OnMouseWheelForward(self, interactor, event):
        maxSlice = self.img3D.GetDimensions()[self.sliceOrientation]
        shift = interactor.GetShiftKey()
        advance = 1
        if shift:
            advance = 10
            
        if (self.sliceno + 10 < maxSlice):
            self.sliceno = self.sliceno + advance
            self.updatePipeline()
        else:
            print ("maxSlice %d request %d" % (maxSlice, self.sliceno + 1 ))
    
    def OnMouseWheelBackward(self, interactor, event):
        minSlice = 0
        shift = interactor.GetShiftKey()
        advance = 1
        if shift:
            advance = 10
        if (self.sliceno - advance >= minSlice):
            self.sliceno = self.sliceno - advance
            self.updatePipeline()
        else:
            print ("minSlice %d request %d" % (minSlice, self.sliceno + 1 ))
        
    def OnKeyPress(self, interactor, event):
        #print ("Pressed key %s" % interactor.GetKeyCode())
        # Slice Orientation 
        if interactor.GetKeyCode() == "X":
            # slice on the other orientation
            self.sliceOrientation = SLICE_ORIENTATION_YZ
            self.sliceno = int(self.img3D.GetDimensions()[1] / 2)
            self.updatePipeline()
        elif interactor.GetKeyCode() == "Y":
            # slice on the other orientation
            self.sliceOrientation = SLICE_ORIENTATION_XZ
            self.sliceno = int(self.img3D.GetDimensions()[1] / 2)
            self.updatePipeline()
        elif interactor.GetKeyCode() == "Z":
            # slice on the other orientation
            self.sliceOrientation = SLICE_ORIENTATION_XY
            self.sliceno = int(self.img3D.GetDimensions()[2] / 2)
            self.updatePipeline()
        if interactor.GetKeyCode() == "x":
            # Change the camera view point
            camera = vtk.vtkCamera()
            camera.SetFocalPoint(self.ren.GetActiveCamera().GetFocalPoint())
            camera.SetViewUp(self.ren.GetActiveCamera().GetViewUp())
            newposition = [i for i in self.ren.GetActiveCamera().GetFocalPoint()]
            newposition[SLICE_ORIENTATION_YZ] = numpy.sqrt(newposition[SLICE_ORIENTATION_XY] ** 2 + newposition[SLICE_ORIENTATION_XZ] ** 2) 
            camera.SetPosition(newposition)
            camera.SetViewUp(0,0,-1)
            self.ren.SetActiveCamera(camera)
            self.ren.ResetCamera()
            self.ren.Render()
            interactor.SetKeyCode("X")
            self.OnKeyPress(interactor, event)
        elif interactor.GetKeyCode() == "y":
             # Change the camera view point
            camera = vtk.vtkCamera()
            camera.SetFocalPoint(self.ren.GetActiveCamera().GetFocalPoint())
            camera.SetViewUp(self.ren.GetActiveCamera().GetViewUp())
            newposition = [i for i in self.ren.GetActiveCamera().GetFocalPoint()]
            newposition[SLICE_ORIENTATION_XZ] = numpy.sqrt(newposition[SLICE_ORIENTATION_XY] ** 2 + newposition[SLICE_ORIENTATION_YZ] ** 2) 
            camera.SetPosition(newposition)
            camera.SetViewUp(0,0,-1)
            self.ren.SetActiveCamera(camera)
            self.ren.ResetCamera()
            self.ren.Render()
            interactor.SetKeyCode("Y")
            self.OnKeyPress(interactor, event)
        elif interactor.GetKeyCode() == "z":
             # Change the camera view point
            camera = vtk.vtkCamera()
            camera.SetFocalPoint(self.ren.GetActiveCamera().GetFocalPoint())
            camera.SetViewUp(self.ren.GetActiveCamera().GetViewUp())
            newposition = [i for i in self.ren.GetActiveCamera().GetFocalPoint()]
            newposition[SLICE_ORIENTATION_XY] = numpy.sqrt(newposition[SLICE_ORIENTATION_YZ] ** 2 + newposition[SLICE_ORIENTATION_XZ] ** 2) 
            camera.SetPosition(newposition)
            camera.SetViewUp(0,1,0)
            self.ren.SetActiveCamera(camera)
            self.ren.ResetCamera()
            self.ren.Render()
            interactor.SetKeyCode("Z")
            self.OnKeyPress(interactor, event)
        elif interactor.GetKeyCode() == "a":
            # reset color/window
            cmax = self.ia.GetMax()[0]
            cmin = self.ia.GetMin()[0]
            
            self.InitialLevel = (cmax+cmin)/2
            self.InitialWindow = cmax-cmin
            
            self.wl.SetLevel(self.InitialLevel)
            self.wl.SetWindow(self.InitialWindow)
            
            self.wl.Update()
                
            self.sliceActor.Update()
            self.AdjustCamera()
            self.renWin.Render()
            
        else :
            #print ("Unhandled event %s" % (interactor.GetKeyCode(), )))
            pass 
    
    def OnLeftButtonPressEvent(self, interactor, event):
        alt = interactor.GetAltKey()
        shift = interactor.GetShiftKey()
        ctrl = interactor.GetControlKey()
#        print ("alt pressed " + (lambda x : "Yes" if x else "No")(alt))
#        print ("shift pressed " + (lambda x : "Yes" if x else "No")(shift))
#        print ("ctrl pressed " + (lambda x : "Yes" if x else "No")(ctrl))
        
        interactor.SetInitialEventPosition(interactor.GetEventPosition())
        
        if ctrl and not (alt and shift): 
            self.event = ViewerEvent.CREATE_ROI_EVENT
            wsize = self.renWin.GetSize()
            position = interactor.GetEventPosition()
            self.ROIWidget.GetBorderRepresentation().SetPosition((position[0]/wsize[0] - 0.05) , (position[1]/wsize[1] - 0.05))
            self.ROIWidget.GetBorderRepresentation().SetPosition2( (0.1) , (0.1))
            
            self.ROIWidget.On()
            self.renWin.Render()
            print ("Event %s is CREATE_ROI_EVENT" % (event))
        elif alt and not (shift and ctrl):
            self.event = ViewerEvent.DELETE_ROI_EVENT
            self.ROIWidget.Off()
            self.updateCornerAnnotation("", 1, False)
            self.renWin.Render()
            print ("Event %s is DELETE_ROI_EVENT" % (event))
        elif not (ctrl and alt and shift):
            self.event = ViewerEvent.PICK_EVENT
            self.HandlePickEvent(interactor, event)
            print ("Event %s is PICK_EVENT" % (event))
        
            
    
    def OnLeftButtonReleaseEvent(self, interactor, event):
        if self.event == ViewerEvent.CREATE_ROI_EVENT:
            #bc = self.ROIWidget.GetBorderRepresentation().GetPositionCoordinate()
            #print (bc.GetValue())
            self.OnROIModifiedEvent(interactor, event)
            
        elif self.event == ViewerEvent.PICK_EVENT:
            self.HandlePickEvent(interactor, event)
         
        self.event = ViewerEvent.NO_EVENT

    def OnRightButtonPressEvent(self, interactor, event):
        alt = interactor.GetAltKey()
        shift = interactor.GetShiftKey()
        ctrl = interactor.GetControlKey()
#        print ("alt pressed " + (lambda x : "Yes" if x else "No")(alt))
#        print ("shift pressed " + (lambda x : "Yes" if x else "No")(shift))
#        print ("ctrl pressed " + (lambda x : "Yes" if x else "No")(ctrl))
        
        interactor.SetInitialEventPosition(interactor.GetEventPosition())
        
        
        if alt and not (ctrl and shift):
            self.event = ViewerEvent.WINDOW_LEVEL_EVENT
            print ("Event %s is WINDOW_LEVEL_EVENT" % (event))
            self.HandleWindowLevel(interactor, event)
        elif shift and not (ctrl and alt):
            self.event = ViewerEvent.ZOOM_EVENT
            self.style.StartDolly()
            print ("Event %s is ZOOM_EVENT" % (event))
        elif ctrl and not (shift and alt):
            self.event = ViewerEvent.PAN_EVENT
            print ("Event %s is PAN_EVENT" % (event))
        
    def OnRightButtonReleaseEvent(self, interactor, event):
        print (event)
        if self.event == ViewerEvent.WINDOW_LEVEL_EVENT:
            self.InitialLevel = self.wl.GetLevel()
            self.InitialWindow = self.wl.GetWindow()
        elif self.event == ViewerEvent.ZOOM_EVENT:
            self.style.EndDolly()
			
        self.event = ViewerEvent.NO_EVENT
        
    
    def OnROIModifiedEvent(self, interactor, event):
        
        #print ("ROI EVENT " + event)
        p1 = self.ROIWidget.GetBorderRepresentation().GetPositionCoordinate()
        p2 = self.ROIWidget.GetBorderRepresentation().GetPosition2Coordinate()
        wsize = self.renWin.GetSize()
        
        #print (p1.GetValue())
        #print (p2.GetValue())
        pp1 = [p1.GetValue()[0] * wsize[0] , p1.GetValue()[1] * wsize[1] , 0.0]
        pp2 = [p2.GetValue()[0] * wsize[0] + pp1[0] , p2.GetValue()[1] * wsize[1] + pp1[1] , 0.0]
        vox1 = self.viewport2imageCoordinate(pp1)
        vox2 = self.viewport2imageCoordinate(pp2)
        
        self.ROI = (vox1 , vox2)
        #print ("Pixel1 %d,%d,%d Value %f" % vox1 )
        #print ("Pixel2 %d,%d,%d Value %f" % vox2 )
        x = self.ROI[1][0] - self.ROI[0][0]
        y = self.ROI[1][1] - self.ROI[0][1]
        text = "ROI: %d x %d, %d Mp" % (x,y,x*y/1024/1024)
        print (text)
        self.updateCornerAnnotation(text, 1)
        self.event = ViewerEvent.NO_EVENT
        
    def viewport2imageCoordinate(self, viewerposition):
        #Determine point index
        
        self.picker.Pick(viewerposition[0], viewerposition[1], 0.0, self.GetRenderer())
        pickPosition = list(self.picker.GetPickPosition())
        pickPosition[self.sliceOrientation] = \
            self.img3D.GetSpacing()[self.sliceOrientation] * self.sliceno + \
            self.img3D.GetOrigin()[self.sliceOrientation]
        print ("Pick Position " + str (pickPosition))
        
        if (pickPosition != [0,0,0]):
            dims = self.img3D.GetDimensions()
            print (dims)
            spac = self.img3D.GetSpacing()
            orig = self.img3D.GetOrigin()
            imagePosition = [int(pickPosition[i] / spac[i] + orig[i]) for i in range(3) ]

#            imagePositionZ = int(pointIndex / (dims[0] * dims[1]))
#            imagePositionY = int((pointIndex - (imagePositionZ * dims[0] * dims[1])) / dims[0])
#            imagePositionX = int(pointIndex - (imagePositionZ*dims[0]*dims[1]) - (imagePositionY*dims[0]))
            
            pixelValue = self.img3D.GetScalarComponentAsDouble(imagePosition[0], imagePosition[1], imagePosition[2], 0)
            return (imagePosition[0], imagePosition[1], imagePosition[2] , pixelValue)
        else:
            return (0,0,0,0)

        
    
    def GetRenderWindow(self):
        return self.renWin
    
    def OnMouseMoveEvent(self, interactor, event):        
        if self.event == ViewerEvent.WINDOW_LEVEL_EVENT:
            print ("Event %s is WINDOW_LEVEL_EVENT" % (event))
            self.HandleWindowLevel(interactor, event)    
        elif self.event == ViewerEvent.PICK_EVENT:
            self.HandlePickEvent(interactor, event)
        elif self.event == ViewerEvent.ZOOM_EVENT:
            self.HandleZoomEvent(interactor, event)
            
            
    def HandleZoomEvent(self, interactor, event):
        dx,dy = interactor.GetDeltaEventPosition()   
        size = self.GetRenderWindow().GetSize()
        dy = 4 * dy / size[0]
        print ("distance: " + str(self.ren.GetActiveCamera().GetDistance()))
        
        print ("camera dolly %f" % (1 + dy))
        newCamera = False
        if newCamera:
            camera = vtk.vtkCamera()
            camera.SetFocalPoint(self.ren.GetActiveCamera().GetFocalPoint())
            cpos = self.ren.GetActiveCamera().GetPosition()
            print ("current position " + str(cpos))
            camera.SetViewUp(self.ren.GetActiveCamera().GetViewUp())
            camera.SetPosition(cpos)
            newposition = [i for i in self.ren.GetActiveCamera().GetFocalPoint()]
            
            delta = newposition[self.sliceOrientation] - cpos[self.sliceOrientation]
            newposition[self.sliceOrientation] = newposition[self.sliceOrientation] + (1+dy) * delta
            print ("new position " + str(newposition))
            camera.SetPosition(newposition)
            #camera.SetViewUp(0,1,0)
            #camera.Dolly(1+dy)
            self.ren.SetActiveCamera(camera)
            self.ren.ResetCamera()
        else :
            self.style.Dolly(1+dy)
#            self.ren.GetActiveCamera().Dolly(1 + dy)
#            
#            if self.style.GetAutoAdjustCameraClippingRange():
#                self.ren.ResetCameraClippingRange()
#                print ("autoadjust clipping range")
#            else:
#                cam = self.ren.GetActiveCamera()
#                bounds = self.sliceActor.GetBounds()
#                spos = bounds[self.sliceOrientation * 2]
#                cpos = cam.GetPosition()[self.sliceOrientation]
#                crange = abs(spos - cpos);
#                spacing = self.img3D.GetSpacing()
#                avg_spacing = (spacing[0] + spacing[1] + spacing[2]) / 3.0
#                cam.SetClippingRange(	crange - avg_spacing * 3.0, crange + avg_spacing * 3.0)
			
		
            
            #self.ren.GetActiveCamera().SetDistance(self.ren.GetActiveCamera().GetDistance()*(1+dy))
            #self.ren.ResetCamera()
        print ("distance after: " + str(self.ren.GetActiveCamera().GetDistance()))
        self.ren.Render()
    
    def HandleWindowLevel(self, interactor, event):
        dx,dy = interactor.GetDeltaEventPosition()
        print ("Event delta %d %d" % (dx,dy))
        size = self.GetRenderWindow().GetSize()
        
        dx = 4 * dx / size[0]
        dy = 4 * dy / size[1]
        window = self.InitialWindow
        level = self.InitialLevel
        
        if abs(window) > 0.01:
            dx = dx * window
        else:
            dx = dx * (lambda x: -0.01 if x <0 else 0.01)(window);
			
        if abs(level) > 0.01:
            dy = dy * level
        else:
            dy = dy * (lambda x: -0.01 if x <0 else 0.01)(level)
			

        # Abs so that direction does not flip

        if window < 0.0:
            dx = -1*dx
        if level < 0.0:
            dy = -1*dy

		 # Compute new window level

        newWindow = dx + window
        newLevel = level - dy

        # Stay away from zero and really

        if abs(newWindow) < 0.01:
            newWindow = 0.01 * (lambda x: -1 if x <0 else 1)(newWindow)

        if abs(newLevel) < 0.01:
            newLevel = 0.01 * (lambda x: -1 if x <0 else 1)(newLevel)

        self.wl.SetWindow(newWindow)
        self.wl.SetLevel(newLevel)
        
        self.wl.Update()
        self.sliceActor.Update()
        self.AdjustCamera()
        
        self.renWin.Render()
    
    def HandlePickEvent(self, interactor, event):
        position = interactor.GetEventPosition()
        #print ("PICK " + str(position))
        vox = self.viewport2imageCoordinate(position)
        #print ("Pixel %d,%d,%d Value %f" % vox )
        self.cornerAnnotation.VisibilityOn()
        self.cornerAnnotation.SetText(0, "[%d,%d,%d] : %.2f" % vox)
        self.iren.Render()
        
    def updateCornerAnnotation(self, text , idx=0, visibility=True):
        if visibility:
            self.cornerAnnotation.VisibilityOn()
        else:
            self.cornerAnnotation.VisibilityOff()
            
        self.cornerAnnotation.SetText(idx, text)
        self.iren.Render()