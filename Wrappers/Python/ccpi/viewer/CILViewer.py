# -*- coding: utf-8 -*-
#   Copyright 2017 Edoardo Pasca
#   Copyright 2018 Richard Smith
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
import os
#from ccpi.viewer import ViewerEventManager
from ccpi.viewer.CILViewer2D import ViewerEventManager

from ccpi.viewer.CILViewer2D import SLICE_ORIENTATION_XY, SLICE_ORIENTATION_XZ, \
   SLICE_ORIENTATION_YZ, CONTROL_KEY, SHIFT_KEY, ALT_KEY, SLICE_ACTOR, \
   OVERLAY_ACTOR, HISTOGRAM_ACTOR, HELP_ACTOR, CURSOR_ACTOR, CROSSHAIR_ACTOR,\
   LINEPLOT_ACTOR

from ccpi.viewer.utils import colormaps

class CILInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self, callback):
        vtk.vtkInteractorStyleTrackballCamera.__init__(self)
        self._viewer = callback
        self.AddObserver('MouseWheelForwardEvent', self.mouseInteraction, 1.0)
        self.AddObserver('MouseWheelBackwardEvent', self.mouseInteraction, 1.0)
        self.AddObserver('KeyPressEvent', self.keyPress, 1.0)
        self.AddObserver('LeftButtonPressEvent', self.OnLeftMouseClick, 0.3)
        self.AddObserver('LeftButtonReleaseEvent', self.OnLeftMouseRelease,0.3)
        self.AddObserver('RightButtonPressEvent', self.OnRightMousePress)
        self.AddObserver('RightButtonReleaseEvent', self.OnRightMouseRelease)
        self.AddObserver('MouseMoveEvent', self.OnMouseMoveEvent, 1.)

        self.InitialEventPosition = (0,0)

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
        if not decimate.GetInput() is None:
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
            # print (self.GetActiveSlice())
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
        shift = interactor.GetShiftKey()
        print (alt, ctrl,shift)
        if alt and not (ctrl and shift):
            self._viewer.linePlotActor.VisibilityOn()
            self.SetInitialEventPosition(interactor.GetEventPosition())
            self.SetEventActive("WINDOW_LEVEL_EVENT")
            self.HandleWindowLevel(interactor, event)
        if not (alt and ctrl and shift):
            self.SetEventActive("ZOOM_EVENT")

    def OnRightMouseRelease(self, interactor, event):
        ctrl = interactor.GetControlKey()
        alt = interactor.GetAltKey()
        shift = interactor.GetShiftKey()

        # print (alt, ctrl,shift)
        if alt and not (ctrl and shift):
            self.SetEventInactive("WINDOW_LEVEL_EVENT")
            self._viewer.linePlotActor.VisibilityOff()
        if not (alt and ctrl and shift):
            self.SetEventInactive("ZOOM_EVENT")

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
            
        elif interactor.GetKeyCode() == "r":
            filename = "current_render"
            self.SaveRender(filename)
        elif interactor.GetKeyCode() == "v":
            # toggle visibility of the volume render
            if self._viewer.volume.GetVisibility():
                self._viewer.volume.VisibilityOff()
            else:
                self._viewer.volume.VisibilityOn()
            self._viewer.updatePipeline()
        elif interactor.GetKeyCode() == "s":
            # toggle visibility of the slice 
            
            if self._viewer.sliceActor.GetVisibility():
                self._viewer.sliceActor.VisibilityOff()
            else:
                self._viewer.sliceActor.VisibilityOn()
            self._viewer.updatePipeline()
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
                             "  - YZ Plane: x\n"
                             "  - XZ Plane: y\n"
                             "  - XY Plane: z\n"
                             "  - Save render to current_render.png: r\n"
                             "  - Toggle visibility of volume render: v\n"
                             "  - Toggle visibility of slice: s\n"
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
    def SaveRender(self, filename):
        self._viewer.saveRender(filename)

    def HandleWindowLevel(self, interactor, event):
        
        self._viewer.linePlotActor.VisibilityOn()
        dx,dy = interactor.GetDeltaEventPosition()
        #self.log ("Event delta %d %d" % (dx,dy))
        size = self.GetRenderWindow().GetSize()
        print ("Event delta %d %d" % (dx,dy))
        dx = 1 * dx / size[0]
        dy = 1 * dy / size[1]
        print ("Event delta %d %d" % (dx,dy))
        if hasattr(self, 'InitialWindow'):
            window = self.InitialWindow
        else:
            window = self._viewer.wl.GetWindow()
        if hasattr(self, 'InitialLevel'):
            level = self.InitialLevel
        else:
            level = self._viewer.wl.GetLevel()

        if abs(window) > 0.01:
            dx = dx * window
        else:
            dx = dx * (lambda x: -0.01 if x <0 else 0.01)(window)

        if abs(level) > 0.01:
            dy = dy * level
        else:
            dy = dy * (lambda x: -0.01 if x <0 else 0.01)(level)


        # Abs so that direction does not flip

        if window < 0.0:
            dx = -1*dx
        if level < 0.0:
            dy = -1*dy
        print (dx,dy)
        # Compute new window level
        newWindow = window + dx
        newLevel  = level + dy

        # Stay away from zero and really small numbers
        if abs(newWindow) < 0.01:
            newWindow = 0.01 * (lambda x: -1 if x <0 else 1)(newWindow)

        if abs(newLevel) < 0.01:
            newLevel = 0.01 * (lambda x: -1 if x <0 else 1)(newLevel)

        # change volume render opacity
        
        self._viewer.volume_colormap_limits = (newLevel - newWindow/2, newLevel+ newWindow/2)
        self._viewer.updatePipeline()
        #self._viewer.wl.SetWindow(newWindow)
        self.InitialWindow = newWindow
        #self._viewer.wl.SetLevel(newLevel)
        self.InitialLevel = newLevel
        self.log("current w {} l {}".format(newLevel, newWindow))
    def log(self, msg):
        return self._viewer.log(msg)
    def GetDeltaEventPosition(self):
        x,y = self.GetInteractor().GetEventPosition()
        return (x - self.InitialEventPosition[0] , y - self.InitialEventPosition[1])
    def GetInteractor(self):
        # TODO place in parent class
        return self._viewer.iren
    def SetInitialEventPosition(self, xy):
        self.InitialEventPosition = xy
    def GetRenderWindow(self):
        return self._viewer.getRenderWindow()
    def OnMouseMoveEvent(self, interactor, event):

        if self.GetViewerEvent("WINDOW_LEVEL_EVENT"):
            self.HandleWindowLevel(interactor, event)

class CILViewer():
    '''Simple 3D Viewer based on VTK classes'''
    
    def __init__(self, dimx=600,dimy=600, renWin=None, iren=None, ren=None, debug=True):
        '''creates the rendering pipeline'''

        # Handle arguments
        self.debug = debug
        if renWin is not None:
            self.renWin = renWin
        else:
            self.renWin = vtk.vtkRenderWindow()

        if iren is not None:
            self.iren = iren
        else:
            self.iren = vtk.vtkRenderWindowInteractor()
        
        # create a rendering window and renderer
        if ren is not None: 
            self.ren = ren
        else:
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


        # volume render
        volumeMapper = vtk.vtkSmartVolumeMapper()
        #volumeMapper = vtk.vtkFixedPointVolumeRayCastMapper()
        self.volume_mapper = volumeMapper

        volumeProperty = vtk.vtkVolumeProperty()
        self.volume_property = volumeProperty

        
        # The volume holds the mapper and the property and
        # can be used to position/orient the volume.
        volume = vtk.vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)
        self.volume = volume


        # an actor for XY plots
        self.linePlotActorInstalled = 0
        self.linePlotActor = vtk.vtkXYPlotActor()
        self.linePlotActor.ExchangeAxesOff()
        self.linePlotActor.SetXTitle( "" )
        self.linePlotActor.SetYTitle( "" )
        self.linePlotActor.SetXLabelFormat( "%.0f" )
        self.linePlotActor.SetYLabelFormat( "%.0f" )
        #self.linePlotActor.SetAdjustXLabels(3)
        #self.linePlotActor.SetXTitle( "Level" )
        #self.linePlotActor.SetYTitle( "N" )
        self.linePlotActor.SetXValuesToValue()
        # histogram plot
        self.linePlotActor.SetPlotColor(0, (1,0,0.5) )
        # plot the limits
        self.linePlotActor.SetPlotColor(1, (1,1,0) )
        self.linePlotActor.SetPlotColor(2, (1,1,0) )

        self.linePlotActor.SetPosition(0,0.1)
        self.linePlotActor.SetPosition2(1,0.4)

        # Makes sure that x axis only goes as far as the number of pixels in the image
        self.linePlotActor.SetAdjustXLabels(0)

        self.iah = vtk.vtkImageAccumulate()
        
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
            

    def startRenderLoop(self):
        self.iren.Start()

    def setInput3DData(self, imageData):
        self.img3D = imageData
        self.installPipeline()

    def setInputData(self, imageData):
        '''alias of setInput3DData'''
        return self.setInput3DData(imageData)

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
        try:
            N = self.ren.GetActors().GetNumberOfItems()
            i = 0
            while i < N:
                actor = self.ren.GetActors().GetNextActor()
                self.ren.RemoveActor(actor)
                i += 1
        except TypeError as te:
            print (te)
            print (self.ren.GetActors())

        self.installSliceActorPipeline()
        self.installVolumeRenderActorPipeline()
        self.installHistogramPlotPipeline()

        self.ren.ResetCamera()
        self.ren.Render()

        self.adjustCamera()

        self.iren.Initialize()
        self.renWin.Render()

    def installVolumeRenderActorPipeline(self):
        
        self.volume_mapper.SetInputData(self.img3D)

        ia = vtk.vtkImageHistogramStatistics()
        ia.SetInputData(self.img3D)
        ia.SetAutoRangePercentiles(90.,99.)
        ia.Update()
        
        cmin, cmax = ia.GetAutoRange()
        print ("viewer: cmin cmax", cmin, cmax)
        # cmin, cmax = (1000,2000)
        # probably the level could be the median of the image within
        # the percentiles 
        median = ia.GetMedian()
        # accomodates all values between the level an the percentiles
        #window = 2*max(abs(median-cmin),abs(median-cmax))
        window = cmax - cmin
        viridis = colormaps.CILColorMaps.get_color_transfer_function('viridis', (cmin,cmax))

        x = numpy.linspace(ia.GetMinimum(), ia.GetMaximum(), num=255)
        scaling = 0.1
        opacity = colormaps.CILColorMaps.get_opacity_transfer_function(x, 
          colormaps.relu, cmin, cmax, scaling)

        self.volume_property.SetColor(viridis)
        self.volume_property.SetScalarOpacity(opacity)
        self.volume_property.ShadeOn()
        self.volume_property.SetInterpolationTypeToLinear()

        self.ren.AddVolume(self.volume)
        self.volume_colormap_limits = (cmin, cmax)
        
    def installHistogramPlotPipeline(self):
        #use 255 bins

        self.iah.SetInputData(self.img3D)
        delta = self.iah.GetMax()[0] - self.iah.GetMin()[0]
        nbins = 255
        self.iah.SetComponentSpacing(delta/nbins,0,0)
        self.iah.SetComponentExtent(0,nbins,0,0,0,0 )
        self.iah.Update()

        self.linePlotActor.AddDataSetInputConnection(self.iah.GetOutputPort())
        self.linePlotActor.VisibilityOff()
        self.ren.AddActor(self.linePlotActor)


    def installSliceActorPipeline(self):
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
        self.sliceActor.GetProperty().SetOpacity(0.99)
        self.sliceActor.Update()
        self.sliceActor.SetInterpolate(False)
        self.ren.AddActor(self.sliceActor)
        

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
        self.sliceActor.GetProperty().SetOpacity(0.99)
        self.sliceActor.Update()

        no = self.showActor(self.sliceActorNo, self.sliceActor)
        self.sliceActorNo = no

        self.updateVolumePipeline()

        self.adjustCamera(resetcamera)

        self.renWin.Render()

    def updateVolumePipeline(self):
        cmin , cmax = self.volume_colormap_limits
        viridis = colormaps.CILColorMaps.get_color_transfer_function('viridis', (cmin,cmax))

        x = numpy.linspace(self.ia.GetMinimum(), self.ia.GetMaximum(), num=255)
        scaling = 0.1
        opacity = colormaps.CILColorMaps.get_opacity_transfer_function(x, 
          colormaps.relu, cmin, cmax, scaling)
        self.volume_property.SetColor(viridis)
        self.volume_property.SetScalarOpacity(opacity)
        

    def setVolumeColorLevelWindow(self, cmin, cmax):
        self.volume_colormap_limits = (cmin, cmax)
        self.updatePipeline()

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
        
    def saveRender(self, filename, renWin=None):
        '''Save the render window to PNG file'''
        # screenshot code:
        w2if = vtk.vtkWindowToImageFilter()
        if renWin == None:
            renWin = self.renWin
        w2if.SetInput(renWin)
        w2if.Update()

        # Check if user has supplied an extension
        extn = os.path.splitext(filename)[1]
        if extn.lower() == '.png':
                saveFilename = filename
        else:
            saveFilename = filename+'.png'

        writer = vtk.vtkPNGWriter()
        writer.SetFileName(saveFilename)
        writer.SetInputConnection(w2if.GetOutputPort())
        writer.Write()
    
    def log(self, msg):
        if self.debug:
            print(msg)