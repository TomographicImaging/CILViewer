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
import math
from vtk.util import numpy_support

SLICE_ORIENTATION_XY = 2 # Z
SLICE_ORIENTATION_XZ = 1 # Y
SLICE_ORIENTATION_YZ = 0 # X


class ViewerEventManager():

    def __init__(self):
        # If all values are false it signifies no event
        self.events = {
            "PICK_EVENT": False,                # left  mouse
            "WINDOW_LEVEL_EVENT": False,        # alt + right mouse + move
            "ZOOM_EVENT": False,                # shift + right mouse + move
            "PAN_EVENT": False,                 # ctrl + right mouse + move
            "CREATE_ROI_EVENT": False,          # ctrl + left mouse
            "DELETE_ROI_EVENT": False,          # alt + left mouse
            "SHOW_LINE_PROFILE_EVENT": False    # l
        }

    def __str__(self):
        return str(self.events)

    def On(self, event):
        self.events[event] = True

    def Off(self, event):
        self.events[event] = False

    def setAllInactive(self):
        self.events = {x:False for x in self.events}

    def isActive(self, event):
        return self.events[event]

    def isAllInactive(self):
        """Returns True if all events are inactive"""
        return all(not x for x in self.events.values())

class CILInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self, callback):
        vtk.vtkInteractorStyleTrackballCamera.__init__(self)
        self._viewer = callback
        self.AddObserver('MouseWheelForwardEvent', self.mouseInteraction, 1.0)
        self.AddObserver('MouseWheelBackwardEvent', self.mouseInteraction, 1.0)
        self.AddObserver('KeyPressEvent', self.keyPress, 1.0)
        self.AddObserver('LeftButtonPressEvent', self.OnLeftMouseClick)
        self.AddObserver('LeftButtonReleaseEvent', self.OnLeftMouseRelease)
        self.AddObserver('RightButtonPressEvent', self.OnRightMousePress, 1.0)
        self.AddObserver('RightButtonReleaseEvent', self.OnRightMouseRelease, 1.0)

    def GetSliceOrientation(self):
        return self._viewer.sliceOrientation

    def GetDimensions(self):
        return self._viewer.img3D.GetDimensions()

    def GetActiveSlice(self):
        return self._viewer.sliceno

    def SetActiveSlice(self, value):
        self._viewer.sliceno = value

    def UpdatePipeline(self, resetcamera=False):
        self._viewer.updatePipeline(resetcamera)

    def GetSliceActorNo(self):
        return self._viewer.sliceActorNo

    def SetSliceOrientation(self, orientation):
        self._viewer.sliceOrientation = orientation

    def SetActiveCamera(self, camera):
        self._viewer.ren.SetActiveCamera(camera)

    def Render(self):
        self._viewer.renWin.Render()

    def GetKeyCode(self):
        return self.GetInteractor().GetKeyCode()

    def SetKeyCode(self, keycode):
        self.GetInteractor().SetKeyCode(keycode)

    def GetControlKey(self):
        return self.GetInteractor().GetControlKey()

    def GetShiftKey(self):
        return self.GetInteractor().GetShiftKey()

    def GetAltKey(self):
        return self.GetInteractor().GetAltKey()

    def GetEventPosition(self):
        return self.GetInteractor().GetEventPosition()

    def GetActiveCamera(self):
        return self._viewer.ren.GetActiveCamera()

    def SetDecimalisation(self, value):
        decimate = self._viewer.decimate
        decimate.SetTargetReduction(value)
        decimate.Update()

    def SetEventActive(self, event):
        self._viewer.event.On(event)

    def SetEventInactive(self, event):
        self._viewer.event.Off(event)

    def GetViewerEvent(self, event):
        return self._viewer.event.isActive(event)

    def HideActor(self, actorno, delete=False):
        self._viewer.hideActor(actorno, delete)

    def ShowActor(self, actorno):
        self._viewer.showActor(actorno)

    def mouseInteraction(self, interactor, event):
        if event == 'MouseWheelForwardEvent':
            maxSlice = self.GetDimensions()[self.GetSliceOrientation()]
            print (self.GetActiveSlice())
            if (self.GetActiveSlice() + 1 < maxSlice):
                self.SetActiveSlice(self.GetActiveSlice() + 1)
                self.UpdatePipeline()
        else:
            minSlice = 0
            if (self.GetActiveSlice() - 1 > minSlice):
                self.SetActiveSlice(self.GetActiveSlice() -1)
                self.UpdatePipeline()

    def OnLeftMouseClick(self, interactor, event):
        self.SetDecimalisation(0.8)
        self.OnLeftButtonDown()

    def OnLeftMouseRelease(self, interactor, event):
        self.SetDecimalisation(0.0)
        self.OnLeftButtonUp()
    def OnRightMousePress(self, interactor, event):
        ctrl = interactor.GetControlKey()
        alt = interactor.GetAltKey()
        shift = interactor.GetShiftKey

        if alt and not (ctrl and shift):
            self.SetEventActive("WINDOW_LEVEL_EVENT")

    def OnRightMouseRelease(self, interactor, event):
        self.SetEventInactive("WINDOW_LEVEL_EVENT")

    def keyPress(self, interactor, event):

        ctrl = interactor.GetControlKey()
        shift = interactor.GetAltKey()
        alt = interactor.GetShiftKey()

        if interactor.GetKeyCode() == "x":

            self.SetSliceOrientation( SLICE_ORIENTATION_YZ )
            self.SetActiveSlice(int(self.GetDimensions()[0]/2))
            self.UpdatePipeline(resetcamera=True)

        elif interactor.GetKeyCode() == "y":

            self.SetSliceOrientation(SLICE_ORIENTATION_XZ)
            self.SetActiveSlice(int(self.GetDimensions()[2] / 2))
            self.UpdatePipeline(resetcamera=True)

        elif interactor.GetKeyCode() == "z":

            self.SetSliceOrientation(SLICE_ORIENTATION_XY)
            self.SetActiveSlice(int(self.GetDimensions()[2] / 2))
            self.UpdatePipeline(resetcamera=True)

        elif ctrl and not (alt and shift):
            # CREATE ROI
            position = interactor.GetEventPosition()
            print ("3D VIEWER MOUSE POSITION", position)


        elif alt and not (shift and ctrl):
            # DELETE ROI
            print ("DELETE ROI")

        elif interactor.GetKeyCode() == "h":
            self.DisplayHelp()

        else:
            print("Unhandled event %s" % interactor.GetKeyCode())

    def DisplayHelp(self):
        help_actor = self._viewer.helpActor
        slice_actor = self._viewer.sliceActor


        if help_actor.GetVisibility():
            help_actor.VisibilityOff()
            slice_actor.VisibilityOn()
            self.ShowActor(1)
            self.Render()
            return

        font_size = 24

        # Create the text mappers and the associated Actor2Ds.

        # The font and text properties (except justification) are the same for
        # each multi line mapper. Let's create a common text property object
        multiLineTextProp = vtk.vtkTextProperty()
        multiLineTextProp.SetFontSize(font_size)
        multiLineTextProp.SetFontFamilyToArial()
        multiLineTextProp.BoldOn()
        multiLineTextProp.ItalicOn()
        multiLineTextProp.ShadowOn()
        multiLineTextProp.SetLineSpacing(1.3)

        # The text is on multiple lines and center-justified (both horizontal and
        # vertical).
        textMapperC = vtk.vtkTextMapper()
        textMapperC.SetInput("Mouse Interactions:\n"
                             "\n"
                             "  - Slice: Mouse Scroll\n"
                             "  - Pan: Ctrl + Right Mouse + Move\n"
                             "  - Adjust Camera: Left Mouse + Move\n"
                             "  - Rotate: Ctrl + Left Mouse + Move"
                             "\n"
                             "Keyboard Interactions:\n"
                             "\n"
                             "  - YZ Plane: X\n"
                             "  - XZ Plane: Y\n"
                             "  - XY Plane: Z\n"
                             )
        tprop = textMapperC.GetTextProperty()
        tprop.ShallowCopy(multiLineTextProp)
        tprop.SetJustificationToLeft()
        tprop.SetVerticalJustificationToCentered()
        tprop.SetColor(0, 1, 0)

        help_actor.SetMapper(textMapperC)
        help_actor.VisibilityOn()
        slice_actor.VisibilityOff()
        self.HideActor(1)

        self.Render()

class CILViewer():
    '''Simple 3D Viewer based on VTK classes'''
    
    def __init__(self, dimx=600,dimy=600, renWin=None, iren=None):
        '''creates the rendering pipeline'''

        # Handle arguments
        if renWin:
            self.renWin = renWin
        else:
            self.renWin = vtk.vtkRenderWindow()

        if iren:
            self.iren = iren
        else:
            self.iren = vtk.vtkRenderWindowInteractor()
        
        # create a rendering window and renderer
        self.ren = vtk.vtkRenderer()
        self.renWin.SetSize(dimx,dimy)
        self.renWin.AddRenderer(self.ren)

        # img 3D as slice
        self.img3D = None
        self.sliceno = 0
        self.sliceOrientation = SLICE_ORIENTATION_XY
        self.sliceActor = vtk.vtkImageActor()
        self.voi = vtk.vtkExtractVOI()
        self.wl = vtk.vtkImageMapToWindowLevelColors()
        self.ia = vtk.vtkImageHistogramStatistics()
        self.sliceActorNo = 0

        # Viewer Event manager
        self.event = ViewerEventManager()

        # create a renderwindowinteractor
        self.style = CILInteractorStyle(self)
        self.iren.SetInteractorStyle(self.style)
        self.iren.SetRenderWindow(self.renWin)

        # Render decimation
        self.decimate = vtk.vtkDecimatePro()

        self.ren.SetBackground(.1, .2, .4)

        self.actors = {}

        # Help text
        self.helpActor = vtk.vtkActor2D()
        self.helpActor.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
        self.helpActor.GetPositionCoordinate().SetValue(0.1, 0.5)
        self.helpActor.VisibilityOff()
        self.ren.AddActor(self.helpActor)
        
        self.iren.Initialize()

    def getRenderer(self):
        '''returns the renderer'''
        return self.ren

    def GetSliceOrientation(self):
        return self.sliceOrientation

    def getRenderWindow(self):
        '''returns the render window'''
        return self.renWin

    def getInteractor(self):
        '''returns the render window interactor'''
        return self.iren

    def getCamera(self):
        '''returns the active camera'''
        return self.ren.GetActiveCamera()

    def createPolyDataActor(self, polydata):
        '''returns an actor for a given polydata'''

        self.decimate.SetInputData(polydata)
        self.decimate.SetTargetReduction(0.0)
        self.decimate.Update()

        mapper = vtk.vtkPolyDataMapper()
        if vtk.VTK_MAJOR_VERSION <= 5:
            mapper.SetInput(polydata)
        else:
            mapper.SetInputConnection(self.decimate.GetOutputPort())
        # actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        #actor.GetProperty().SetOpacity(0.8)
        return actor

    def setPolyDataActor(self, actor):
        '''displays the given polydata'''

        self.hideActor(1,delete=True)
        self.ren.AddActor(actor)

        self.actors[len(self.actors)+1] = [actor, True]
        self.iren.Initialize()
        self.renWin.Render()

    def displayPolyData(self, polydata):
        self.setPolyDataActor(self.createPolyDataActor(polydata))

    def hideActor(self, actorno, delete=False):
        '''Hides an actor identified by its number in the list of actors'''
        try:
            if self.actors[actorno][1]:
                self.ren.RemoveActor(self.actors[actorno][0])
                self.actors[actorno][1] = False

            if delete:
                self.actors = {}
                self.renWin.Render()

        except KeyError as ke:
            print ("Warning Actor not present")
        
    def showActor(self, actorno, actor = None):
        '''Shows hidden actor identified by its number in the list of actors'''
        try:
            if not self.actors[actorno][1]:
                self.ren.AddActor(self.actors[actorno][0])
                self.actors[actorno][1] = True
                return actorno
        except KeyError as ke:
            # adds it to the actors if not there already
            if actor != None:
                self.ren.AddActor(actor)
                self.actors[len(self.actors)+1] = [actor, True]
                return len(self.actors)

    def addActor(self, actor):
        '''Adds an actor to the render'''
        return self.showActor(0, actor)
            
    def saveRender(self, filename, renWin=None):
        '''Save the render window to PNG file'''
        # screenshot code:
        w2if = vtk.vtkWindowToImageFilter()
        if renWin == None:
            renWin = self.renWin
        w2if.SetInput(renWin)
        w2if.Update()
         
        writer = vtk.vtkPNGWriter()
        writer.SetFileName("%s.png" % (filename))
        writer.SetInputConnection(w2if.GetOutputPort())
        writer.Write()

    def startRenderLoop(self):
        self.iren.Start()

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
            doubleImg.AllocateScalars(vtk.VTK_DOUBLE,1)
            
            for i in range(shape[0]):
                for j in range(shape[1]):
                    for k in range(shape[2]):
                        doubleImg.SetScalarComponentFromDouble(
                            i,j,k,0, numpyarray[i][j][k])

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

    def installPipeline(self):
        # Reset the viewer when loading a new data source
        for actor in self.ren.GetActors():
            self.ren.RemoveActor(actor)

        self.voi.SetInputData(self.img3D)

        extent = [ i for i in self.img3D.GetExtent()]
        extent[self.sliceOrientation * 2] = self.sliceno
        extent[self.sliceOrientation * 2 + 1] = self.sliceno
        self.voi.SetVOI(extent[0], extent[1],
                   extent[2], extent[3],
                   extent[4], extent[5])

        self.voi.Update()

        self.ia.SetInputData(self.voi.GetOutput())
        self.ia.SetAutoRangePercentiles(1.0, 99.)
        self.ia.Update()

        cmin, cmax = self.ia.GetAutoRange()
        # probably the level could be the median of the image within
        # the percentiles
        level = self.ia.GetMedian()
        # accomodates all values between the level an the percentiles
        window = 2 * max(abs(level - cmin), abs(level - cmax))

        self.InitialLevel = level
        self.InitialWindow = window

        self.wl.SetLevel(self.InitialLevel)
        self.wl.SetWindow(self.InitialWindow)

        self.wl.SetInputData(self.voi.GetOutput())
        self.wl.Update()

        self.sliceActor.SetInputData(self.wl.GetOutput())
        self.sliceActor.SetDisplayExtent(extent[0], extent[1],
                                         extent[2], extent[3],
                                         extent[4], extent[5])
        self.sliceActor.Update()
        self.sliceActor.SetInterpolate(False)
        self.ren.AddActor(self.sliceActor)
        self.ren.ResetCamera()
        self.ren.Render()

        self.adjustCamera()

        self.iren.Initialize()
        self.renWin.Render()

    def updatePipeline(self, resetcamera = False):
        self.hideActor(self.sliceActorNo)

        extent = [i for i in self.img3D.GetExtent()]
        extent[self.sliceOrientation * 2] = self.sliceno
        extent[self.sliceOrientation * 2 + 1] = self.sliceno
        self.voi.SetVOI(extent[0], extent[1],
                   extent[2], extent[3],
                   extent[4], extent[5])

        self.voi.Update()
        self.ia.Update()
        self.wl.Update()

        # Set image actor
        self.sliceActor.SetInputData(self.wl.GetOutput())
        self.sliceActor.SetDisplayExtent(extent[0], extent[1],
                                    extent[2], extent[3],
                                    extent[4], extent[5])
        self.sliceActor.Update()

        no = self.showActor(self.sliceActorNo, self.sliceActor)
        self.sliceActorNo = no

        self.adjustCamera(resetcamera)

        self.renWin.Render()

    def adjustCamera(self, resetcamera= False):

        self.ren.ResetCameraClippingRange()

        if resetcamera:
            self.ren.ResetCamera()

    # Set interpolation on
    def setInterpolateOn(self):
        self.sliceActor.SetInterpolate(True)
        self.renWin.Render()

    # Set interpolation off
    def setInterpolateOff(self):
        self.sliceActor.SetInterpolate(False)
        self.renWin.Render()

    def setColourWindowLevel(self, window, level):
        self.wl.SetWindow(window)
        self.wl.SetLevel(level)
        self.wl.Update()
        self.sliceActor.SetInputData(self.wl.GetOutput())
        self.sliceActor.Update()
        self.ren.Render()
        self.renWin.Render()


