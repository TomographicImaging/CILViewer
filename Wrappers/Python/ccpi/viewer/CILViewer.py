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
   
import glob
import os
import re

import numpy
import vtk
from ccpi.viewer.CILViewer2D import (ALT_KEY, CONTROL_KEY, CROSSHAIR_ACTOR,
                                     CURSOR_ACTOR, HELP_ACTOR, HISTOGRAM_ACTOR,
                                     LINEPLOT_ACTOR, OVERLAY_ACTOR, SHIFT_KEY,
                                     SLICE_ACTOR, SLICE_ORIENTATION_XY,
                                     SLICE_ORIENTATION_XZ,
                                     SLICE_ORIENTATION_YZ, ViewerEventManager)
from ccpi.viewer.utils import colormaps
from ccpi.viewer.utils.io import SaveRenderToPNG


class CILInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self, callback):
        vtk.vtkInteractorStyleTrackballCamera.__init__(self)
        self._viewer = callback
        self.AddObserver('MouseWheelForwardEvent', self.mouseInteraction, 1.0)
        self.AddObserver('MouseWheelBackwardEvent', self.mouseInteraction, 1.0)
        self.AddObserver('KeyPressEvent', self.OnKeyPress, 1.0)
        self.AddObserver('LeftButtonPressEvent', self.OnLeftMouseClick)
        self.AddObserver('LeftButtonReleaseEvent', self.OnLeftMouseRelease)
        #self.AddObserver('RightButtonPressEvent', self.OnRightMousePress, -0.5)
        #self.AddObserver('RightButtonReleaseEvent', self.OnRightMouseRelease, -0.5)

    def GetSliceOrientation(self):
        return self._viewer.sliceOrientation

    def GetDimensions(self):
        return self._viewer.img3D.GetDimensions()

    def GetActiveSlice(self):
        return self._viewer.getActiveSlice()

    def SetActiveSlice(self, sliceno):
        self._viewer.setActiveSlice(sliceno)

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
    
    def SetInitialLevel(self, level):
        self._viewer.InitialLevel = level

    def GetInitialLevel(self):
        return self._viewer.InitialLevel

    def SetInitialWindow(self, window):
        self._viewer.InitialWindow = window

    def GetInitialWindow(self):
        return self._viewer.InitialWindow

    def HideActor(self, actorno, delete=False):
        self._viewer.hideActor(actorno, delete)

    def ShowActor(self, actorno):
        self._viewer.showActor(actorno)

    def mouseInteraction(self, interactor, event):
        shift = interactor.GetShiftKey()
        advance = 1
        if shift:
            advance = 10

        if event == 'MouseWheelForwardEvent':
            maxSlice = self._viewer.img3D.GetExtent()[self.GetSliceOrientation()*2+1]
            # print (self.GetActiveSlice())
            if (self.GetActiveSlice() + advance <= maxSlice):
                self.SetActiveSlice(self.GetActiveSlice() + advance)
                self.UpdatePipeline()
        else:
            minSlice = self._viewer.img3D.GetExtent()[self.GetSliceOrientation()*2]
            if (self.GetActiveSlice() - advance >= minSlice):
                self.SetActiveSlice(self.GetActiveSlice() - advance)
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
        # print (alt, ctrl,shift)
        if alt and not (ctrl and shift):
            self.SetEventActive("WINDOW_LEVEL_EVENT")
        if not (alt and ctrl and shift):
            self.SetEventActive("ZOOM_EVENT")

    def OnRightMouseRelease(self, interactor, event):
        ctrl = interactor.GetControlKey()
        alt = interactor.GetAltKey()
        shift = interactor.GetShiftKey()

        # print (alt, ctrl,shift)
        if alt and not (ctrl and shift):
            self.SetEventInactive("WINDOW_LEVEL_EVENT")
        if not (alt and ctrl and shift):
            self.SetEventInactive("ZOOM_EVENT")

    def OnKeyPress(self, interactor, event):

        ctrl = interactor.GetControlKey()
        shift = interactor.GetAltKey()
        alt = interactor.GetShiftKey()

        if interactor.GetKeyCode() == "x":
            self.SetSliceOrientation( SLICE_ORIENTATION_YZ )
            self.UpdatePipeline(resetcamera=True)

        elif interactor.GetKeyCode() == "y":
            self.SetSliceOrientation(SLICE_ORIENTATION_XZ)
            self.UpdatePipeline(resetcamera=True)

        elif interactor.GetKeyCode() == "z":
            self.SetSliceOrientation(SLICE_ORIENTATION_XY)
            self.UpdatePipeline(resetcamera=True)

        elif interactor.GetKeyCode() == "a":
            # reset color/window
            cmin, cmax = self._viewer.ia.GetAutoRange()

            # set the level to the average value between the percintiles
            level = (cmin + cmax) / 2
            # accommodates all values between the level an the percentiles
            window = (cmax - cmin) / 2

            self.SetInitialLevel(level)
            self.SetInitialWindow(window)

            self._viewer.imageSlice.GetProperty().SetColorLevel(self.GetInitialLevel())
            self._viewer.imageSlice.GetProperty().SetColorWindow(self.GetInitialWindow())

            self._viewer.imageSlice.Update()
            self.Render()

        elif ctrl and not (alt and shift):
            # CREATE ROI
            position = interactor.GetEventPosition()
            # print ("3D VIEWER MOUSE POSITION", position)


        # elif alt and not (shift and ctrl):
        #     # DELETE ROI
        #     print ("DELETE ROI")

        elif interactor.GetKeyCode() == "h":
            self.DisplayHelp()
            
        elif interactor.GetKeyCode() == "r":
            filename = "current_render"
            self.SaveRender(filename)
        elif interactor.GetKeyCode() == "v":
            # toggle visibility of the volume render
            if not self._viewer.volume_render_initialised:
                self._viewer.installVolumeRenderActorPipeline()

            if self._viewer.volume.GetVisibility():
                self._viewer.volume.VisibilityOff()
                self._viewer.light.SwitchOff()
            else:
                self._viewer.volume.VisibilityOn()
                self._viewer.light.SwitchOn()
            self._viewer.updatePipeline()
        elif interactor.GetKeyCode() == "s":
            # toggle visibility of the slice 
            
            if self._viewer.imageSlice.GetVisibility():
                self._viewer.imageSlice.VisibilityOff()
            else:
                self._viewer.imageSlice.VisibilityOn()
            self._viewer.updatePipeline()
        elif interactor.GetKeyCode() == "i":
            # toggle interpolation of image slice
            is_interpolated = self._viewer.imageSlice.GetProperty().GetInterpolationType()
            if is_interpolated:
                self._viewer.imageSlice.GetProperty().SetInterpolationTypeToNearest()
            else:
                self._viewer.imageSlice.GetProperty().SetInterpolationTypeToLinear()
            self._viewer.updatePipeline()
        elif interactor.GetKeyCode() == "c" and self._viewer.volume_render_initialised:
            viewer = self._viewer
            viewer.imageSlice.VisibilityOff() 
            # clip a volume render if available
            if hasattr(self._viewer, 'planew'):   
                is_enabled = viewer.planew.GetEnabled()
                viewer.planew.SetEnabled(not is_enabled)
                # print ("should set to not", is_enabled)
                viewer.getRenderer().Render()
            else:
                # print ("handling c")
                planew = vtk.vtkImplicitPlaneWidget2()
                
                rep = vtk.vtkImplicitPlaneRepresentation()
                world_extent = self.GetImageWorldExtent()
                extent = [0, world_extent[0], 0, world_extent[1], 0, world_extent[2]]
                rep.SetWidgetBounds(*extent)
                planew.SetInteractor(viewer.getInteractor())
                planew.SetRepresentation(rep)

                rep.SetNormalToCamera()
                rep.SetOutlineTranslation(False) # this means user can't move bounding box

                plane = vtk.vtkPlane()
                # should be in the focal point
                cam = self.GetActiveCamera()
                foc = cam.GetFocalPoint()
                plane.SetOrigin( *foc )
                
                proj = cam.GetDirectionOfProjection()
                proj = [x + 0.3 for x in list(proj)]
                plane.SetNormal( *proj )
                rep.SetPlane(plane)
                rep.UpdatePlacement()

                viewer.volume.GetMapper().AddClippingPlane(plane)
                viewer.volume.Modified()
                planew.On()
                viewer.plane = plane
                viewer.planew = planew
                planew.AddObserver('InteractionEvent', self.update_clipping_plane, 0.5)
            viewer.updatePipeline()
        else:
            print("Unhandled event %s" % interactor.GetKeyCode())
    def update_clipping_plane(self, interactor, event):
        # event translator should you want to filter events
        # event_translator = planew.GetEventTranslator()
        # pevent = event_translator.GetTranslation(event)
        planew = self._viewer.planew
        viewer = self._viewer
        rep = planew.GetRepresentation()
        plane = vtk.vtkPlane()
        rep.GetPlane(plane)
        
        viewer.volume.GetMapper().RemoveAllClippingPlanes()
        viewer.volume.GetMapper().AddClippingPlane(plane)
        viewer.volume.Modified()
        viewer.getRenderer().Render()


    def DisplayHelp(self):
        help_actor = self._viewer.helpActor
        slice_actor = self._viewer.imageSlice


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
                             "  - Zoom: Right Mouse + Move Up/Down\n"
                             "  - Pan: Middle Mouse Button + Move or Shift + Left Mouse + Move\n"
                             "  - Adjust Camera: Left Mouse + Move\n"
                             "  - Rotate: Ctrl + Left Mouse + Move\n"
                             "\n"
                             "Keyboard Interactions:\n"
                             "\n"
                             "h: Display this help\n"
                             "x:  YZ Plane\n"
                             "y:  XZ Plane\n"
                             "z:  XY Plane\n"
                             "r:  Save render to current_render.png\n"
                             "s:  Toggle visibility of slice\n"
                             "v:  Toggle visibility of volume render\n"
                             "c:  Activates volume render clipping plane widget\n"
                             "a:  Whole image Auto Window/Level\n"
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

    # Coordinate conversion ----------------------------

    def world2imageCoordinate(self, world_coordinates):
        """
        Convert from the world or global coordinates to image coordinates
        :param world_coordinates: (x,y,z)
        :return: rounded to next integer (x,y,z) in image coorindates eg. slice index
        """

        dims = self.GetInputData().GetDimensions()
        self.log(dims)
        spac = self.GetInputData().GetSpacing()
        orig = self.GetInputData().GetOrigin()

        return [round((world_coordinates[i]) / spac[i] - orig[i]) for i in range(3)]
    
    def world2imageCoordinateFloat(self, world_coordinates):
        """
        Convert from the world or global coordinates to image coordinates
        :param world_coordinates: (x,y,z)
        :return: float (x,y,z) in image coorindates eg. slice index
        """

        dims = self.GetInputData().GetDimensions()
        self.log(dims)
        spac = self.GetInputData().GetSpacing()
        orig = self.GetInputData().GetOrigin()

        return [(world_coordinates[i]) / spac[i] - orig[i]  for i in range(3)]

    def image2world(self, image_coordinates):

        spac = self.GetInputData().GetSpacing()
        orig = self.GetInputData().GetOrigin()

        return [(image_coordinates[i]) * spac[i] + orig[i] for i in range(3)]

    def GetImageWorldExtent(self):
        """
        Compute and return the maximum extent of the image in the rendered world
        """
        return self.image2world(self.GetInputData().GetExtent()[1::2])
    
    
    def GetInputData(self):
        return self._viewer.img3D

class CILViewer():
    '''Simple 3D Viewer based on VTK classes'''
    
    def __init__(self, dimx=600,dimy=600, renWin=None, iren=None, ren=None, debug=False):
        '''creates the rendering pipeline'''

        # Handle arguments
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
        self.slicenos = [0,0,0]
        self.sliceOrientation = SLICE_ORIENTATION_XY


        imageSlice = vtk.vtkImageSlice()
        imageSliceMapper = vtk.vtkImageSliceMapper()
        imageSlice.SetMapper(imageSliceMapper)
        imageSlice.GetProperty().SetInterpolationTypeToNearest()
        self.imageSlice = imageSlice
        self.imageSliceMapper = imageSliceMapper

        self.voi = vtk.vtkExtractVOI()
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
        self.volume_colormap_name = 'viridis'
        self.volume_render_initialised = False
        
        # axis orientation widget
        om = vtk.vtkAxesActor()
        ori = vtk.vtkOrientationMarkerWidget()
        ori.SetOutlineColor( 0.9300, 0.5700, 0.1300 )
        ori.SetInteractor(self.iren)
        ori.SetOrientationMarker(om)
        ori.SetViewport( 0.0, 0.0, 0.4, 0.4 )
        ori.SetEnabled(1)
        ori.InteractiveOff()
        self.orientation_marker = ori

        self.iren.Initialize()

    def getRenderer(self):
        '''returns the renderer'''
        return self.ren

    def GetSliceOrientation(self):
        return self.sliceOrientation

    def getActiveSlice(self):
        return self.slicenos[self.GetSliceOrientation()]

    def setActiveSlice(self, sliceno):
        self.slicenos[self.GetSliceOrientation()] = sliceno

    def getRenderWindow(self):
        '''returns the render window'''
        return self.renWin

    def getInteractor(self):
        '''returns the render window interactor'''
        return self.iren

    def getCamera(self):
        '''returns the active camera'''
        return self.ren.GetActiveCamera()

    def getColourWindow(self):
        return self.imageSlice.GetProperty().GetColorWindow()
    
    def getColourLevel(self):
        return self.imageSlice.GetProperty().GetColorLevel()

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
        # self.installVolumeRenderActorPipeline()

        self.ren.ResetCamera()
        self.ren.Render()

        self.adjustCamera()

        self.iren.Initialize()
        self.renWin.Render()

    def installVolumeRenderActorPipeline(self):
        
        self.volume_mapper.SetInputData(self.img3D)

        # define colors and opacity with default values
        colors, opacity = self.getColorOpacityForVolumeRender()

        self.volume_property.SetColor(colors)
        if self.getVolumeRenderOpacityMethod() == 'gradient':
            self.volume_property.SetGradientOpacity(opacity)
        elif self.getVolumeRenderOpacityMethod() == 'scalar':
            self.volume_property.SetScalarOpacity(opacity)
        else:
            # currently this is not relevant, but in the future one may want to do 
            # something fancier
            # see also https://www.kitware.com/new-in-paraview-5-9-volume-rendering-with-a-separate-opacity-array/
            self.volume_property.SetGradientOpacity(opacity)
                        
        self.volume_property.ShadeOn()
        self.volume_property.SetInterpolationTypeToLinear()

        self.ren.AddVolume(self.volume)
        self.volume_render_initialised = True
        self.volume.VisibilityOff()
        self.addHeadlight()
        
    def addHeadlight(self):
        lgt = vtk.vtkLight()
        lgt.SetLightTypeToHeadlight()
        lgt.SwitchOff()
        self.getRenderer().AddLight(lgt)
        self.light = lgt
    
    def getVolumeRenderOpacityMethod(self):
        if not hasattr(self, '_vol_render_opacity_method'):
            self.setVolumeRenderOpacityMethod('gradient')
        return self._vol_render_opacity_method
    def setVolumeRenderOpacityMethod(self, method='gradient'):
        if method in ['scalar', 'gradient']:
            self._vol_render_opacity_method = method
        # if the method is not supported it does nothing???

    def getColorOpacityForVolumeRender(self, percentiles=(80.,99.), color_num=255, max_opacity=0.1):
        '''Defines the color and opacity tables
        
        Parameters:
        :param percentiles: tuple
        :color_num: int, number of colors in the map
        :max_opacity: float in [0,1] representing the maximum rendered opacity'''

        ia = vtk.vtkImageHistogramStatistics()
        ia.SetInputData(self.img3D)
        ia.SetAutoRangePercentiles( *percentiles )
        ia.Update()
        
        cmin, cmax = ia.GetAutoRange()
        self.volume_colormap_limits = (cmin, cmax)
        
        # accomodates all values between the level an the percentiles
        colors = colormaps.CILColorMaps.get_color_transfer_function(self.getVolumeColorMapName(), (cmin,cmax))

        x = numpy.linspace(ia.GetMinimum(), ia.GetMaximum(), num=color_num)
        
        opacity = colormaps.CILColorMaps.get_opacity_transfer_function(x, 
          colormaps.relu, cmin, cmax, max_opacity)

        return colors, opacity
    
    def setVolumeColorMapName(self, cmap='magma'):
        '''set the volume color map name
        
        :param cmap: string with one of ['viridis', 'plasma', 'magma', 'inferno'], or matplotlib's cmaps if available'''
        self.volume_colormap_name = cmap


    def getVolumeColorMapName(self):
        '''get the volume color map name'''
        return self.volume_colormap_name
        

    def installSliceActorPipeline(self):
        self.voi.SetInputData(self.img3D)

        extent = [ i for i in self.img3D.GetExtent()]
        for i in range(len(self.slicenos)):
            self.slicenos[i] = round((extent[i * 2+1] + extent[i * 2])/2)
        extent[self.sliceOrientation * 2] = self.getActiveSlice()
        extent[self.sliceOrientation * 2 + 1] = self.getActiveSlice()

        self.voi.SetVOI(extent[0], extent[1],
                   extent[2], extent[3],
                   extent[4], extent[5])

        self.voi.Update()

        self.ia.SetInputData(self.voi.GetOutput())
        self.ia.SetAutoRangePercentiles(5.0, 95.)
        self.ia.Update()

        cmin, cmax = self.ia.GetAutoRange()
        # set the level to the average between the percentiles 
        level = (cmin + cmax)/2
        # accomodates all values between the level an the percentiles
        window = (cmax - cmin)/2

        self.InitialLevel = level
        self.InitialWindow = window

        self.imageSliceMapper.SetInputConnection(self.voi.GetOutputPort())
        self.imageSlice.Update()

        self.imageSlice.GetProperty().SetColorLevel(self.InitialLevel)
        self.imageSlice.GetProperty().SetColorWindow(self.InitialWindow)
        self.imageSlice.GetProperty().SetInterpolationTypeToNearest()
        self.imageSlice.GetProperty().SetOpacity(0.99)

        self.imageSlice.Update()

        self.ren.AddActor(self.imageSlice)
        

    def updatePipeline(self, resetcamera = False):
        self.hideActor(self.sliceActorNo)

        extent = [i for i in self.img3D.GetExtent()]
        extent[self.sliceOrientation * 2] = self.getActiveSlice()
        extent[self.sliceOrientation * 2 + 1] = self.getActiveSlice()
        self.voi.SetVOI(extent[0], extent[1],
                   extent[2], extent[3],
                   extent[4], extent[5])

        self.voi.Update()
        self.ia.Update()

        self.imageSliceMapper.SetOrientation(self.sliceOrientation)
        self.imageSlice.Update()

        no = self.showActor(self.sliceActorNo, self.imageSlice)
        self.sliceActorNo = no

        self.updateVolumePipeline()

        self.adjustCamera(resetcamera)

        self.renWin.Render()

    def updateVolumePipeline(self):
        if self.volume_render_initialised and self.volume.GetVisibility():
            cmin , cmax = self.volume_colormap_limits
            colors = colormaps.CILColorMaps.get_color_transfer_function(self.volume_colormap_name, (cmin,cmax))

            x = numpy.linspace(self.ia.GetMinimum(), self.ia.GetMaximum(), num=255)
            scaling = 0.1
            opacity = colormaps.CILColorMaps.get_opacity_transfer_function(x, 
            colormaps.relu, cmin, cmax, scaling)
            self.volume_property.SetColor(colors)
            self.volume_property.SetScalarOpacity(opacity)
        

    def setVolumeColorLevelWindow(self, cmin, cmax):
        self.volume_colormap_limits = (cmin, cmax)
        self.updatePipeline()

    def setVolumeColorName(self, name):
        self.volume_colormap_name = name
        self.updatePipeline()

    def getVolumeColorName(self):
        return self.volume_colormap_name

    def adjustCamera(self, resetcamera= False):

        self.ren.ResetCameraClippingRange()

        if resetcamera:
            self.ren.ResetCamera()

    # Set interpolation on
    def setInterpolateOn(self):
        self._viewer.imageSlice.GetProperty().SetInterpolationTypeToLinear()
        self.renWin.Render()

    # Set interpolation off
    def setInterpolateOff(self):
        self._viewer.imageSlice.GetProperty().SetInterpolationTypeToNearest()
        self.renWin.Render()

    def setColourWindowLevel(self, window, level):
        self.imageSlice.GetProperty().SetColorLevel(level)
        self.imageSlice.GetProperty().SetColorWindow(window)
        self.imageSlice.Update()
        self.ren.Render()
        self.renWin.Render()
        
    def saveRender(self, filename, renWin=None):
        '''Save the render window to PNG file'''
        if renWin == None:
            renWin = self.renWin
        SaveRenderToPNG(self.renWin, filename)
