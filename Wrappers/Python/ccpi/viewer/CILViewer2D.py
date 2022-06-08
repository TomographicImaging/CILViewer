# -*- coding: utf-8 -*-
#   Copyright 2017 - 2019 Edoardo Pasca
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
import glob, re

from ccpi.viewer.utils import Converter
from ccpi.viewer.utils.io import SaveRenderToPNG

SLICE_ORIENTATION_XY = 2  # Z
SLICE_ORIENTATION_XZ = 1  # Y
SLICE_ORIENTATION_YZ = 0  # X

CONTROL_KEY = 8
SHIFT_KEY = 4
ALT_KEY = -128

SLICE_ACTOR = 'slice_actor'
OVERLAY_ACTOR = 'overlay_actor'
HISTOGRAM_ACTOR = 'histogram_actor'
HELP_ACTOR = 'help_actor'
CURSOR_ACTOR = 'cursor_actor'
CROSSHAIR_ACTOR = 'crosshair_actor'
LINEPLOT_ACTOR = 'lineplot_actor'
WIPE_ACTOR = 'wipe_actor'


class ViewerEventManager(object):

    def __init__(self):
        # If all values are false it signifies no event
        self.events = {
            "PICK_EVENT": False,  # left  mouse
            "WINDOW_LEVEL_EVENT": False,  # alt + right mouse + move
            "ZOOM_EVENT": False,  # shift + right mouse + move
            "PAN_EVENT": False,  # ctrl + right mouse + move
            "CREATE_ROI_EVENT": False,  # ctrl + left mouse
            "DELETE_ROI_EVENT": False,  # alt + left mouse
            "SHOW_LINE_PROFILE_EVENT": False,  # l
            "UPDATE_WINDOW_LEVEL_UNDER_CURSOR": False,  # Mouse move + w
            "RECTILINEAR_WIPE": False  # activated by key 2, updates by mouse move
        }

    def __str__(self):
        return str(self.events)

    def On(self, event):
        self.events[event] = True

    def Off(self, event):
        self.events[event] = False

    def setAllInactive(self):
        self.events = {x: False for x in self.events}

    def isActive(self, event):
        return self.events[event]

    def isAllInactive(self):
        """Returns True if all events are inactive"""
        return all(not x for x in self.events.values())


class CILInteractorStyle(vtk.vtkInteractorStyle):

    def __init__(self, callback):
        self.callback = callback
        self._viewer = callback
        priority = 1.0
        self.debug = False

        self.AddObserver("MouseWheelForwardEvent", self.OnMouseWheelForward, priority)
        self.AddObserver("MouseWheelBackwardEvent", self.OnMouseWheelBackward, priority)
        self.AddObserver('KeyPressEvent', self.OnKeyPress, priority)
        self.AddObserver('KeyReleaseEvent', self.OnKeyRelease, priority)
        self.AddObserver('LeftButtonPressEvent', self.OnLeftButtonPressEvent, priority)
        self.AddObserver('RightButtonPressEvent', self.OnRightButtonPressEvent, priority)
        self.AddObserver('LeftButtonReleaseEvent', self.OnLeftButtonReleaseEvent, priority)
        self.AddObserver('RightButtonReleaseEvent', self.OnRightButtonReleaseEvent, priority)
        self.AddObserver('MouseMoveEvent', self.OnMouseMoveEvent, priority)

        self.InitialEventPosition = (0, 0)

        # Initialise difference from zoom event start point
        self.dy = 0

        self._reslicing_enabled = True

    @property
    def reslicing_enabled(self):
        return self._reslicing_enabled

    @reslicing_enabled.setter
    def reslicing_enabled(self, value):
        if isinstance(value, bool):
            self._reslicing_enabled = value

    def log(self, msg):
        if self.debug:
            print(msg)

    def SetInitialEventPosition(self, xy):
        self.InitialEventPosition = xy

    def GetInitialEventPosition(self):
        return self.InitialEventPosition

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

    def GetDeltaEventPosition(self):
        x, y = self.GetInteractor().GetEventPosition()
        return (x - self.InitialEventPosition[0], y - self.InitialEventPosition[1])

    def Dolly(self, factor):
        self.callback.camera.Dolly(factor)
        self.callback.ren.ResetCameraClippingRange()

    def GetDimensions(self):
        return self._viewer.img3D.GetDimensions()

    def GetInputData(self):
        return self._viewer.img3D

    def GetSliceOrientation(self):
        return self._viewer.sliceOrientation

    def SetSliceOrientation(self, orientation):
        self._viewer.sliceOrientation = orientation

    def GetActiveSlice(self):
        return self._viewer.getActiveSlice()

    def SetActiveSlice(self, sliceno):
        self._viewer.setActiveSlice(sliceno)

    def UpdatePipeline(self, reset=False):
        self._viewer.updatePipeline(reset)

    def GetActiveCamera(self):
        return self._viewer.ren.GetActiveCamera()

    def SetActiveCamera(self, camera):
        self._viewer.ren.SetActiveCamera(camera)

    def ResetCamera(self):
        self._viewer.ren.ResetCamera()

    def FlipCameraPosition(self, flip=True):
        self._viewer.flipCameraPosition = flip

    def Render(self):
        self._viewer.renWin.Render()

    def UpdateImageSlice(self):
        self._viewer.imageSlice.Update()

    def AdjustCamera(self):
        self._viewer.AdjustCamera()

    def SaveRender(self, filename):
        self._viewer.saveRender(filename)

    def GetRenderWindow(self):
        return self._viewer.renWin

    def GetRenderer(self):
        return self._viewer.ren

    def GetROIWidget(self):
        return self._viewer.ROIWidget

    def SetEventActive(self, event):
        self._viewer.event.On(event)

    def SetEventInactive(self, event):
        self._viewer.event.Off(event)

    def GetViewerEvent(self, event):
        return self._viewer.event.isActive(event)

    def SetInitialCameraPosition(self, position):
        self._viewer.InitialCameraPosition = position

    def GetInitialCameraPosition(self):
        return self._viewer.InitialCameraPosition

    def SetInitialLevel(self, level):
        self._viewer.InitialLevel = level

    def GetInitialLevel(self):
        return self._viewer.InitialLevel

    def SetInitialWindow(self, window):
        self._viewer.InitialWindow = window

    def GetInitialWindow(self):
        return self._viewer.InitialWindow

    def SetROI(self, roi):
        self._viewer.ROI = roi

    def GetROI(self):
        return self._viewer.ROI

    def GetVisualisationDownsampling(self):
        return self._viewer.visualisation_downsampling

    def SetVisualisationDownsampling(self, value):
        self._viewer.setVisualisationDownsampling(value)

    def CreateAnnotationText(self, display_type, data):
        return self._viewer.createAnnotationText(display_type, data)

    def UpdateCornerAnnotation(self, text, corner):
        self._viewer.updateCornerAnnotation(text, corner)

    def GetPicker(self):
        return self._viewer.picker

    def GetCornerAnnotation(self):
        return self._viewer.cornerAnnotation

    def UpdateROIHistogram(self):
        self._viewer.updateROIHistogram()

    def UpdateLinePlot(self, imagecoordinate, display):
        self._viewer.updateLinePlot(imagecoordinate, display)

    def GetCrosshairs(self):
        actor = self._viewer.crosshairsActor
        vert = self._viewer.vertLine
        horiz = self._viewer.horizLine

        return actor, vert, horiz

    def GetImageWorldExtent(self):
        """
        Compute and return the maximum extent of the image in the rendered world
        """
        return self.image2world(self.GetInputData().GetExtent()[1::2])

    def SetCharEvent(self, char):
        self.GetInteractor().SetKeyCode(char)
        self.OnKeyPress(self.GetInteractor(), "KeyPressEvent")

    def validateValue(self, value, axis):
        return self._viewer.validateValue(value, axis)

    def _truncateBox(self, start_pos, world_max_array, axis):
        """
        Make sure that the value for the upper corner of the box is within the world extent.

        :param start_pos: Lower left corner value on specified axis
        :param world_max_array: Array containing (x,y,z) of the maximum extent of the world
        :param axis: The axis of interest eg. "x"
        :return: The start position + a percentage of the world truncated to the edges of the world
        """

        # Set up scale factor and get index for axis
        scale_factor = 0.3
        axis_dict = {"x": 0, "y": 1, "z": 2}
        axis_int = axis_dict[axis]

        # Create the upper right coordinate point with scale offset
        value = start_pos + world_max_array[axis_int] * scale_factor

        # Check to make sure that it is within the image world.
        if value > world_max_array[axis_int]:
            return world_max_array[axis_int]
        else:
            return value

    def InitialiseBox(self, clickPosition):
        """
        Set the initial values for the box borders
        :param clickPosition: Display coordinates for the mouse event
        """

        # Current render orientation
        orientation = self.GetSliceOrientation()

        # Scale factor for initial box
        scale_factor = 0.3

        # Translate the mouse click display coordinates into world coordinates
        coord = vtk.vtkCoordinate()
        coord.SetCoordinateSystemToDisplay()
        coord.SetValue(clickPosition[0], clickPosition[1])
        world_mouse_pos = coord.GetComputedWorldValue(self.GetRenderer())

        # Get maximum extents of the image in world coords
        world_image_max = self.GetImageWorldExtent()

        # Set the minimum world value
        world_image_min = (0, 0, 0)

        # Initialise the box position in format [xmin, xmax, ymin, ymax,...]
        box_pos = [0, 0, 0, 0, 0, 0]

        # place the mouse click as bottom left in current orientation
        if orientation == 2:
            # Looking along z
            # Lower left is xmin, ymin
            box_pos[0] = world_mouse_pos[0]
            box_pos[2] = world_mouse_pos[1]

            # Set top right point
            # Top right is xmax, ymax
            box_pos[1] = self._truncateBox(box_pos[0], world_image_max, "x")
            box_pos[3] = self._truncateBox(box_pos[2], world_image_max, "y")

            # Set the scroll axis to maximum extent eg. min-max
            # zmin, zmax
            box_pos[4] = world_image_min[2]
            box_pos[5] = world_image_max[2]

        elif orientation == 1:
            # Looking along y
            # Lower left is xmin, zmin
            box_pos[0] = world_mouse_pos[0]
            box_pos[4] = world_mouse_pos[2]

            # Set top right point.
            # Top right is xmax, zmax
            box_pos[1] = self._truncateBox(box_pos[0], world_image_max, "x")
            box_pos[5] = self._truncateBox(box_pos[4], world_image_max, "z")

            # Set the scroll axis to maximum extent eg. min-max
            # ymin, ymax
            box_pos[2] = world_image_min[1]
            box_pos[3] = world_image_max[1]

        else:
            # orientation == 0
            # Looking along x
            # Lower left is ymin, zmin
            box_pos[2] = world_mouse_pos[1]
            box_pos[4] = world_mouse_pos[2]

            # Set top right point
            # Top right is ymax, zmax
            box_pos[3] = self._truncateBox(box_pos[2], world_image_max, "y")
            box_pos[5] = self._truncateBox(box_pos[4], world_image_max, "z")

            # Set the scroll axis to maximum extent eg. min-max
            # xmin, xmax
            box_pos[0] = world_image_min[0]
            box_pos[1] = world_image_max[0]

        # Set widget placement and make visible
        self._viewer.ROIWidget.PlaceWidget(box_pos)
        self._viewer.ROIWidget.On()
        self.UpdatePipeline()

    ############### Handle events
    def OnMouseWheelForward(self, interactor, event):
        if self.GetInputData() is None:
            return
        maxSlice = self.GetInputData().GetExtent()[self.GetSliceOrientation() * 2 + 1]
        shift = interactor.GetShiftKey()
        advance = 1
        if shift:
            advance = 10

        if (self.GetActiveSlice() + advance <= maxSlice):
            self.SetActiveSlice(self.GetActiveSlice() + advance)

            self.UpdatePipeline()
        else:
            self.log("maxSlice %d request %d" % (maxSlice, self.GetActiveSlice()))

        if self.GetViewerEvent("SHOW_LINE_PROFILE_EVENT"):
            self.DisplayLineProfile(interactor, event, True)

    def OnMouseWheelBackward(self, interactor, event):
        if self.GetInputData() is None:
            return
        minSlice = self.GetInputData().GetExtent()[self.GetSliceOrientation() * 2]
        shift = interactor.GetShiftKey()
        advance = 1
        if shift:
            advance = 10
        if (self.GetActiveSlice() - advance >= minSlice):
            self.SetActiveSlice(self.GetActiveSlice() - advance)
            self.UpdatePipeline()
        else:
            self.log("minSlice %d request %d" % (minSlice, self.GetActiveSlice()))
        if self.GetViewerEvent("SHOW_LINE_PROFILE_EVENT"):
            self.DisplayLineProfile(interactor, event, True)

    def AutoWindowLevel(self):
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

        self.UpdateImageSlice()
        self.AdjustCamera()
        self.Render()

    def OnKeyPress(self, interactor, event):
        if self.GetInputData() is None:
            return
        if self.reslicing_enabled and interactor.GetKeyCode() == "x":
            # Change the camera view point

            orientation = self.GetSliceOrientation()
            camera = vtk.vtkCamera()
            camera.ParallelProjectionOn()
            camera.SetFocalPoint(self.GetActiveCamera().GetFocalPoint())
            camera.SetPosition(self.GetActiveCamera().GetPosition())
            self.SetInitialCameraPosition(self.GetActiveCamera().GetPosition())
            camera.SetViewUp(self.GetActiveCamera().GetViewUp())

            # Rotation of camera depends on current orientation:
            if orientation == SLICE_ORIENTATION_XY:
                camera.Azimuth(270)
            elif orientation == SLICE_ORIENTATION_XZ:
                self.FlipCameraPosition(True)
                camera.Azimuth(90)
            camera.SetViewUp(0, -1, 0)

            self.SetActiveCamera(camera)
            self.SetSliceOrientation(SLICE_ORIENTATION_YZ)
            self.UpdatePipeline(True)

        elif self.reslicing_enabled and interactor.GetKeyCode() == "y":
            # Change the camera view point

            orientation = self.GetSliceOrientation()

            camera = vtk.vtkCamera()
            camera.ParallelProjectionOn()
            camera.SetFocalPoint(self.GetActiveCamera().GetFocalPoint())
            camera.SetPosition(self.GetActiveCamera().GetPosition())
            self.SetInitialCameraPosition(self.GetActiveCamera().GetPosition())
            camera.SetViewUp(self.GetActiveCamera().GetViewUp())

            # Rotation of camera depends on current orientation:
            if orientation == SLICE_ORIENTATION_XY:
                camera.Elevation(90)
                self.FlipCameraPosition(True)

            elif orientation == SLICE_ORIENTATION_YZ:
                self.FlipCameraPosition(True)
                camera.Elevation(90)

            camera.SetViewUp(0, 0, -1)
            self.SetActiveCamera(camera)
            self.SetSliceOrientation(SLICE_ORIENTATION_XZ)
            self.UpdatePipeline(True)

        elif self.reslicing_enabled and interactor.GetKeyCode() == "z":
            # Change the camera view point

            orientation = self.GetSliceOrientation()
            camera = vtk.vtkCamera()
            camera.ParallelProjectionOn()
            camera.SetPosition(self.GetActiveCamera().GetPosition())
            self.SetInitialCameraPosition(self.GetActiveCamera().GetPosition())
            camera.SetFocalPoint(self.GetActiveCamera().GetFocalPoint())
            camera.SetViewUp(self.GetActiveCamera().GetViewUp())

            # Rotation of camera depends on current orientation:
            if orientation == SLICE_ORIENTATION_YZ:
                camera.Azimuth(90)

            elif orientation == SLICE_ORIENTATION_XZ:
                camera.Elevation(-90)
                self.FlipCameraPosition(True)

            camera.SetViewUp(0, -1, 0)
            self.SetActiveCamera(camera)
            self.ResetCamera()
            self.SetSliceOrientation(SLICE_ORIENTATION_XY)
            self.UpdatePipeline(True)

        elif interactor.GetKeyCode() == "a":
            self.AutoWindowLevel()
        elif interactor.GetKeyCode() == "s":
            filename = "current_render"
            self.SaveRender(filename)

        elif interactor.GetKeyCode() == "q":
            self.log("Render loop terminating by pressing %s" % (interactor.GetKeyCode(), ))
            interactor.SetKeyCode("e")
            self.OnKeyPress(interactor, event)

        elif interactor.GetKeyCode() == "l":
            if self.GetViewerEvent("SHOW_LINE_PROFILE_EVENT"):

                self.SetEventInactive("SHOW_LINE_PROFILE_EVENT")
                self.DisplayLineProfile(interactor, event, False)
            else:
                self.SetEventActive("SHOW_LINE_PROFILE_EVENT")
                self.DisplayLineProfile(interactor, event, True)

        elif interactor.GetKeyCode() == "h":
            self.DisplayHelp()
        elif interactor.GetKeyCode() == "w":
            self.SetEventActive('UPDATE_WINDOW_LEVEL_UNDER_CURSOR')
        elif interactor.GetKeyCode() == "t":
            # tracing event is captured by widget
            if (self._viewer.imageTracer.GetEnabled()):
                self._viewer.imageTracer.Off()
            else:
                self._viewer.imageTracer.On()
        elif interactor.GetKeyCode() == "i":
            # toggle interpolation of slice actor
            is_interpolated = self._viewer.imageSlice.GetProperty().GetInterpolationType()
            if is_interpolated:
                self._viewer.imageSlice.GetProperty().SetInterpolationTypeToNearest()
            else:
                self._viewer.imageSlice.GetProperty().SetInterpolationTypeToLinear()
            self._viewer.updatePipeline()

        elif interactor.GetKeyCode() == '1':
            ev = 'RECTILINEAR_WIPE'
            if self.GetViewerEvent(ev):
                self.SetEventInactive(ev)
            # ImageWithOverlay
            self._viewer.setVisualisationToImageWithOverlay()
            self.AdjustCamera()
            self.Render()

        elif interactor.GetKeyCode() == '2':
            if self._viewer.image2 is not None:
                if self._viewer.vis_mode != CILViewer2D.RECTILINEAR_WIPE:
                    self._viewer.setVisualisationToRectilinearWipe()
                    orient = ['x', 'y', 'z']
                    self.SetCharEvent(orient[self.GetSliceOrientation()])
                    self.SetEventActive('RECTILINEAR_WIPE')

        else:
            self.log("Unhandled event %s" % (interactor.GetKeyCode()))

    def OnKeyRelease(self, interactor, event):
        # remove events on key release
        events = ['UPDATE_WINDOW_LEVEL_UNDER_CURSOR']
        for ev in events:
            if self.GetViewerEvent(ev):
                # print ("remove event {}".format(ev))
                self.SetEventInactive(ev)

    def OnLeftButtonPressEvent(self, interactor, event):
        # print ("INTERACTOR", interactor)
        if self.GetInputData() is None:
            return
        alt = interactor.GetAltKey()
        shift = interactor.GetShiftKey()
        ctrl = interactor.GetControlKey()

        self.SetInitialEventPosition(interactor.GetEventPosition())

        if ctrl and not (alt and shift):
            self.SetEventActive("CREATE_ROI_EVENT")
            position = interactor.GetEventPosition()
            self.InitialiseBox(position)
            self.SetDisplayHistogram(True)
            self.Render()
            self.log("Event %s is CREATE_ROI_EVENT" % (event))

        elif alt and not (shift and ctrl):
            self.SetEventActive("DELETE_ROI_EVENT")
            self.GetROIWidget().Off()
            self._viewer.updateCornerAnnotation("", 1, False)
            self.SetDisplayHistogram(False)
            self.Render()
            self.log("Event %s is DELETE_ROI_EVENT" % (event))

        elif not (ctrl and alt and shift):
            self.SetEventActive("PICK_EVENT")
            self.HandlePickEvent(interactor, event)
            self.log("Event %s is PICK_EVENT" % (event))

    def SetDisplayHistogram(self, display):
        if display:
            if (self._viewer.displayHistogram == 0):
                #self.GetRenderer().AddActor(self._viewer.histogramPlotActor)
                self._viewer.AddActor(self._viewer.histogramPlotActor, HISTOGRAM_ACTOR)
                self.firstHistogram = 1
                self.Render()

            self._viewer.histogramPlotActor.VisibilityOn()
            self._viewer.displayHistogram = True
        else:
            self._viewer.histogramPlotActor.VisibilityOff()
            self._viewer.displayHistogram = False

    def OnLeftButtonReleaseEvent(self, interactor, event):
        interactor = self._viewer.getInteractor()

        if self.GetViewerEvent("CREATE_ROI_EVENT"):
            self.OnROIModifiedEvent(interactor, event)

        elif self.GetViewerEvent("PICK_EVENT"):
            self.HandlePickEvent(interactor, event)

        # Turn off CREATE_ROI and PICK_EVENT
        self.SetEventInactive("CREATE_ROI_EVENT")
        self.SetEventInactive("PICK_EVENT")
        self.SetEventInactive("DELETE_ROI_EVENT")

    def OnRightButtonPressEvent(self, interactor, event):
        if self.GetInputData() is None:
            return
        alt = interactor.GetAltKey()
        shift = interactor.GetShiftKey()
        ctrl = interactor.GetControlKey()

        self.SetInitialEventPosition(interactor.GetEventPosition())

        if alt and not (ctrl and shift):
            self.SetEventActive("WINDOW_LEVEL_EVENT")
            if self._viewer.vis_mode == CILViewer2D.IMAGE_WITH_OVERLAY:
                self.log("Event %s is WINDOW_LEVEL_EVENT" % (event))
                self.HandleWindowLevel(interactor, event)
        elif shift and not (ctrl and alt):
            self.SetEventActive("ZOOM_EVENT")
            self.SetInitialCameraPosition(self.GetActiveCamera().GetPosition())
            self.log("Event %s is ZOOM_EVENT" % (event))
        elif ctrl and not (shift and alt):
            self.SetEventActive("PAN_EVENT")
            self.SetInitialCameraPosition(self.GetActiveCamera().GetPosition())
            self.log("Event %s is PAN_EVENT" % (event))

    def OnRightButtonReleaseEvent(self, interactor, event):
        self.log(event)
        if self.GetViewerEvent("WINDOW_LEVEL_EVENT"):
            if self._viewer.vis_mode == CILViewer2D.IMAGE_WITH_OVERLAY:
                self.SetInitialLevel(self._viewer.imageSlice.GetProperty().GetColorLevel())
                self.SetInitialWindow(self._viewer.imageSlice.GetProperty().GetColorWindow())
        elif self.GetViewerEvent("ZOOM_EVENT") or self.GetViewerEvent("PAN_EVENT"):
            self.SetInitialCameraPosition(())

            # Reset difference from start of zoom event
            self.dy = 0

        # self.SetViewerEvent( ViewerEvent.NO_EVENT )
        self.SetEventInactive("WINDOW_LEVEL_EVENT")
        self.SetEventInactive("ZOOM_EVENT")
        self.SetEventInactive("PAN_EVENT")

    def OnROIModifiedEvent(self, interactor, event):
        # Get bounds from 3D ROI
        pd = vtk.vtkPolyData()
        self.GetROIWidget().GetPolyData(pd)
        bounds = pd.GetBounds()

        # Set the values of the ll and ur corners
        ll = (bounds[0], bounds[2], bounds[4])
        ur = (bounds[1], bounds[3], bounds[5])
        vox1 = self.createVox(ll)
        vox2 = self.createVox(ur)

        # Set the ROI using image coordinates
        self.SetROI((vox1, vox2))
        roi = self.GetROI()

        # Debug messages
        self.log("ROI {0}".format(roi))
        self.log("Pixel1 %d,%d,%d Value %f" % vox1)
        self.log("Pixel2 %d,%d,%d Value %f" % vox2)

        # Calculate the size of the ROI
        if self.GetSliceOrientation() == SLICE_ORIENTATION_XY:
            self.log("slice orientation : XY")
            x = abs(roi[1][0] - roi[0][0])
            y = abs(roi[1][1] - roi[0][1])
            z = abs(roi[1][2] - roi[0][2])

        elif self.GetSliceOrientation() == SLICE_ORIENTATION_XZ:
            self.log("slice orientation : XZ")
            x = abs(roi[1][0] - roi[0][0])
            y = abs(roi[1][2] - roi[0][2])
            z = abs(roi[1][1] - roi[0][1])

        elif self.GetSliceOrientation() == SLICE_ORIENTATION_YZ:
            self.log("slice orientation : YZ")
            x = abs(roi[1][1] - roi[0][1])
            y = abs(roi[1][2] - roi[0][2])
            z = abs(roi[1][1] - roi[0][1])

        # Update the text bottom right of the viewer and histogram
        roi_data = (x, y, z, float(x * y) / 1024.)
        text = self.CreateAnnotationText("roi", roi_data)
        self.log(text)
        self.UpdateCornerAnnotation(text, 1)
        self.UpdateROIHistogram()
        # self.SetViewerEvent( ViewerEvent.NO_EVENT )
        self.SetEventInactive("CREATE_ROI_EVENT")

    def OnTracerModifiedEvent(self, interactor, event):
        # Makes sure tracer is visible on current slice:
        self.UpdatePipeline()

###########################  Coordinate conversion methods ############################

    def display2world(self, displayCoords):
        """
        Takes display coordinates and converts them into world coordinates

        :param displayCoords: tuple containing the X,Y coordinates for the point in the display
        :return: The computed world coordinate of the given point as double (x,y,z)
        """
        coord = vtk.vtkCoordinate()
        coord.SetCoordinateSystemToDisplay()
        coord.SetValue(displayCoords[0], displayCoords[1])

        return coord.GetComputedWorldValue(self.GetRenderer())

    def world2display(self, world_coords):
        """
        Takes coordinates in the world system and converts them to 2D display coordinates
        :param world_coords: (x,y,z) coordinate in the world
        :return: (x,y) screen coordinate
        """

        vc = vtk.vtkCoordinate()
        vc.SetCoordinateSystemToWorld()
        vc.SetValue(world_coords)

        return vc.GetComputedDoubleDisplayValue(self.GetRenderer())

    def display2imageCoordinate(self, viewerposition, subvoxel=False):
        """
        Convert display coordinates into image coordinates and add the pixel value

        :param viewerposition: (x,y) position of the selected point in the display window
        :return: (x,y,z,a) x,y,z index of the selected slice + a, the pixel value
        """
        vc = vtk.vtkCoordinate()
        vc.SetCoordinateSystemToViewport()
        vc.SetValue(viewerposition[0:2] + (0.0, ))

        pickPosition = list(vc.GetComputedWorldValue(self.GetRenderer()))
        # print ("PICK POS", pickPosition)

        pickPosition[self.GetSliceOrientation()] = \
            self.GetInputData().GetSpacing()[self.GetSliceOrientation()]  * (self.GetActiveSlice()) # + self.GetInputData().GetOrigin()[self.GetSliceOrientation()])
        self.log("Pick Position " + str(pickPosition))

        if (pickPosition != [0, 0, 0]):

            imagePosition = self.world2imageCoordinate(pickPosition)
            imagePositionF = self.world2imageCoordinateFloat(pickPosition)
            extent = self._viewer.img3D.GetExtent()

            # make sure the pick is on the image
            if imagePosition[0] < extent[0]:
                imagePosition[0] = extent[0]
            if imagePosition[0] > extent[1]:
                imagePosition[0] = extent[1]
            if imagePosition[1] < extent[2]:
                imagePosition[1] = extent[2]
            if imagePosition[1] > extent[3]:
                imagePosition[1] = extent[3]
            if imagePosition[2] < extent[4]:
                imagePosition[2] = extent[4]
            if imagePosition[2] > extent[5]:
                imagePosition[2] = extent[5]

            self.log("imagePosition pre validate {}".format(imagePosition))

            pixelValue = self.GetInputData().GetScalarComponentAsDouble(imagePosition[0], imagePosition[1],
                                                                        imagePosition[2], 0)
            if self._viewer.rescale[0]:
                scale, shift = self._viewer.rescale[1]
                # pix = orig * scale + shift
                # orig = (-shift + pix) / scale
                pixelValue = (-shift + pixelValue) / scale

            if subvoxel:
                for i in range(3):
                    if not i == self.GetSliceOrientation():
                        imagePosition[i] = imagePositionF[i]

            return (self.validateValue(imagePosition[0], 'x'), self.validateValue(imagePosition[1], 'y'),
                    self.validateValue(imagePosition[2], 'z'), pixelValue)
        else:
            return (0, 0, 0, 0)

    def createVox(self, world_coordinates):

        # Translate the world coordinates to an image index
        imagePosition = self.world2imageCoordinate(world_coordinates)

        pixelValue = self.GetInputData().GetScalarComponentAsDouble(imagePosition[0], imagePosition[1],
                                                                    imagePosition[2], 0)
        if self._viewer.rescale[0]:
            scale, shift = self._viewer.rescale[1]
            pixelValue = (-shift + pixelValue) / scale
        return (self.validateValue(imagePosition[0],
                                   'x'), self.validateValue(imagePosition[1],
                                                            'y'), self.validateValue(imagePosition[2], 'z'), pixelValue)

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

        return [(world_coordinates[i]) / spac[i] - orig[i] for i in range(3)]

    def image2world(self, image_coordinates):
        spac = self.GetInputData().GetSpacing()
        orig = self.GetInputData().GetOrigin()

        return [(image_coordinates[i]) * spac[i] + orig[i] for i in range(3)]

    def imageCoordinate2display(self, imageposition):
        '''
        Convert image coordinates back into viewer coordinates
        :param imageposition: (x,y,z) coordinates in image coordinates
        :return: (x,y,z) coordinates for the window
        '''
        # Truncate to first 3 values x,y,z. Not interested in pixel value.
        ip = imageposition[0:3]

        spac = self.GetInputData().GetSpacing()
        orig = self.GetInputData().GetOrigin()

        # Convert image coordiantes to world coordinates
        world_coord = [spac[i] * (ip[i] - orig[i]) for i in range(3)]

        vc = vtk.vtkCoordinate()
        vc.SetCoordinateSystemToWorld()
        vc.SetValue(world_coord)

        return vc.GetComputedDoubleViewportValue(self.GetRenderer())

    def display2normalisedViewport(self, display_coords):
        wsize = self.GetRenderWindow().GetSize()

        x = display_coords[0] / wsize[0]
        y = display_coords[1] / wsize[1]

        return x, y

    def OnMouseMoveEvent(self, interactor, event):
        if self.GetInputData() is not None:
            if self.GetViewerEvent("WINDOW_LEVEL_EVENT"):
                self.log("Event %s is WINDOW_LEVEL_EVENT" % (event))
                self.HandleWindowLevel(interactor, event)

            elif self.GetViewerEvent("PICK_EVENT"):
                self.HandlePickEvent(interactor, event)

            elif self.GetViewerEvent("ZOOM_EVENT"):
                self.HandleZoomEvent(interactor, event)

            elif self.GetViewerEvent("PAN_EVENT"):
                self.HandlePanEvent(interactor, event)

            elif self.GetViewerEvent("SHOW_LINE_PROFILE_EVENT"):
                self.DisplayLineProfile(interactor, event, True)
            elif self.GetViewerEvent('UPDATE_WINDOW_LEVEL_UNDER_CURSOR'):
                x, y = interactor.GetEventPosition()
                ic = self.display2imageCoordinate((x, y))
                print(x, y, ic, "image coordinate")
                whole_extent = self._viewer.img3D.GetExtent()
                around = numpy.min(numpy.asarray([whole_extent[1], whole_extent[3], whole_extent[5]])) // 10
                print(around, "around")
                extent = [
                    ic[0] - around, ic[0] + around, ic[1] - around, ic[1] + around, ic[2] - around, ic[2] + around
                ]

                orientation = self._viewer.sliceOrientation

                extent[orientation * 2] = self.GetActiveSlice()
                extent[orientation * 2 + 1] = self.GetActiveSlice()

                if extent[0] < whole_extent[0]:
                    extent[0] = whole_extent[0]
                if extent[1] > whole_extent[1]:
                    extent[1] = whole_extent[1]
                if extent[2] < whole_extent[2]:
                    extent[2] = whole_extent[2]
                if extent[3] > whole_extent[3]:
                    extent[3] = whole_extent[3]
                if extent[4] < whole_extent[4]:
                    extent[4] = whole_extent[4]
                if extent[5] > whole_extent[5]:
                    extent[5] = whole_extent[5]
                # get mouse location

                print(*extent, "w extent")
                self._viewer.voicursor.SetInputData(self._viewer.img3D)
                self._viewer.voicursor.SetVOI(*extent)

                self._viewer.voicursor.Update()
                # set window/level for current slices

                self._viewer.iacursor.SetInputConnection(self._viewer.voicursor.GetOutputPort())
                self._viewer.iacursor.SetAutoRangePercentiles(1.0, 99.)
                self._viewer.iacursor.Update()
                # reset color/window
                cmin, cmax = self._viewer.iacursor.GetAutoRange()

                # set the level to the average between the percentiles
                level = (cmin + cmax) / 2
                # accommodates all values between the level an the percentiles
                window = (cmax - cmin) / 2

                self.SetInitialLevel(level)
                self.SetInitialWindow(window)

                self._viewer.imageSlice.GetProperty().SetColorLevel(self.GetInitialLevel())
                self._viewer.imageSlice.GetProperty().SetColorWindow(self.GetInitialWindow())

                self.UpdateImageSlice()
                self.AdjustCamera()
                self.Render()
            elif self.GetViewerEvent('RECTILINEAR_WIPE'):
                # get event in image coordinate
                x, y, z, pix = self.display2imageCoordinate(interactor.GetEventPosition())
                # update the wipe depending on the slice orientation
                slice_orientation = self._viewer.getSliceOrientation()
                if slice_orientation == SLICE_ORIENTATION_XY:
                    self._viewer.wipe.SetAxis(0, 1)
                    self._viewer.wipe.SetPosition(x, y)
                elif slice_orientation == SLICE_ORIENTATION_XZ:
                    self._viewer.wipe.SetAxis(0, 2)
                    self._viewer.wipe.SetPosition(x, z)
                elif slice_orientation == SLICE_ORIENTATION_YZ:
                    self._viewer.wipe.SetAxis(2, 1)
                    self._viewer.wipe.SetPosition(z, y)

                self.UpdatePipeline()

    def DisplayHelp(self):
        help_actor = self._viewer.helpActor
        image_slice = self._viewer.imageSlice

        if help_actor.GetVisibility():
            help_actor.VisibilityOff()
            image_slice.VisibilityOn()
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
                             "  - Quick Slice: Shift + Mouse Scroll\n"
                             "  - Pick: Left Click\n"
                             "  - Zoom: Shift + Right Mouse + Move Up/Down\n"
                             "  - Pan: Ctrl + Right Mouse + Move\n"
                             "  - Adjust Window: Alt+ Right Mouse + Move Up/Down\n"
                             "  - Adjust Level: Alt + Right Mouse + Move Left/Right\n"
                             "  Region of Interest (ROI):\n"
                             "      - Create: Ctrl + Left Click\n"
                             "      - Delete: Alt + Left Click\n"
                             "      - Resize: Click + Drag handles\n"
                             "      - Translate: Middle Mouse + Move within ROI\n"
                             "\n"
                             "Keyboard Interactions:\n"
                             "\n"
                             "  - a: Whole image Auto Window/Level\n"
                             "  - w: Region around cursor Auto Window/Level\n"
                             "  - l: Line Profile at cursor\n"
                             "  - s: Save Current Image\n"
                             "  - x: YZ Plane\n"
                             "  - y: XZ Plane\n"
                             "  - z: XY Plane\n"
                             "  - t: Tracing\n"
                             "  - i: toggle interpolation of slice\n"
                             "  - h: this help\n")
        tprop = textMapperC.GetTextProperty()
        tprop.ShallowCopy(multiLineTextProp)
        tprop.SetJustificationToLeft()
        tprop.SetVerticalJustificationToCentered()
        tprop.SetColor(0, 1, 0)

        help_actor.SetMapper(textMapperC)
        help_actor.VisibilityOn()
        image_slice.VisibilityOff()
        self.Render()

    def HandleZoomEvent(self, interactor, event):
        camera = self.GetActiveCamera()

        # Extract change from start of event
        dx, dy = interactor.GetDeltaEventPosition()
        window_y_size = self.GetRenderWindow().GetSize()[1]

        # Determine whether the user is zooming in or out
        change = dy - self.dy

        # Make sure that a change has been registered
        if change != 0:
            # >1 zoom in, <1 zoom out
            camera.Zoom(1 + change / window_y_size)
            self.Render()

        # Set the overall change value
        self.dy = dy

    def HandlePanEvent(self, interactor, event):
        #Camera uses world coordinates, not display coordinates so we have to make a coneversion
        interactor_event_position = interactor.GetEventPosition()
        interactor_initial_event_position = interactor.GetInitialEventPosition()

        event_position = interactor.image2world(interactor.display2imageCoordinate(interactor_event_position)[:-1])
        initial_event_position = interactor.image2world(
            interactor.display2imageCoordinate(interactor_initial_event_position)[:-1])

        #Update initial position to current event position, ready for next panning event:
        interactor.SetInitialEventPosition(interactor_event_position)

        change = []
        for i in range(len(event_position)):
            change.append(event_position[i] - initial_event_position[i])

        camera = self.GetActiveCamera()

        newposition = [i for i in self.GetInitialCameraPosition()]
        newfocalpoint = [i for i in camera.GetFocalPoint()]

        for i in range(len(event_position)):
            newposition[i] -= change[i]
            newfocalpoint[i] -= change[i]

        camera.SetFocalPoint(newfocalpoint)
        camera.SetPosition(newposition)
        self.SetInitialCameraPosition(newposition)

        self.Render()

    def HandleWindowLevel(self, interactor, event):
        dx, dy = interactor.GetDeltaEventPosition()
        self.log("Event delta %d %d" % (dx, dy))
        size = self.GetRenderWindow().GetSize()

        dx = 1 * dx / size[0]
        dy = 1 * dy / size[1]
        window = self.GetInitialWindow()
        level = self.GetInitialLevel()

        if abs(window) > 0.01:
            dx = dx * window
        else:
            dx = dx * (lambda x: -0.01 if x < 0 else 0.01)(window)

        if abs(level) > 0.01:
            dy = dy * level
        else:
            dy = dy * (lambda x: -0.01 if x < 0 else 0.01)(level)

        # Abs so that direction does not flip

        if window < 0.0:
            dx = -1 * dx
        if level < 0.0:
            dy = -1 * dy

        # Compute new window level
        newWindow = window + dx
        newLevel = level + dy

        # Stay away from zero and really small numbers
        if abs(newWindow) < 0.01:
            newWindow = 0.01 * (lambda x: -1 if x < 0 else 1)(newWindow)

        if abs(newLevel) < 0.01:
            newLevel = 0.01 * (lambda x: -1 if x < 0 else 1)(newLevel)

        self._viewer.imageSlice.GetProperty().SetColorLevel(newLevel)
        self._viewer.imageSlice.GetProperty().SetColorWindow(newWindow)
        self.log("new level {0} window {1}".format(newLevel, newWindow))
        self.UpdateImageSlice()
        self.AdjustCamera()

        self.Render()

    def HandlePickEvent(self, interactor, event):
        position = interactor.GetEventPosition()
        vox = self.display2imageCoordinate(position)
        self.last_picked_voxel = vox
        # print ("Pixel %d,%d,%d Value %f" % vox )
        self._viewer.cornerAnnotation.VisibilityOn()
        text = self.CreateAnnotationText("pick", vox)
        self.UpdateCornerAnnotation(text, 0)
        self.Render()

    def DisplayLineProfile(self, interactor, event, display):
        x, y = interactor.GetEventPosition()
        ic = self.display2imageCoordinate((x, y))
        self.UpdateLinePlot(ic, display)


###############################################################################


class CILViewer2D():
    '''Simple Interactive Viewer based on VTK classes'''
    # visualisation modes
    IMAGE_WITH_OVERLAY = 0
    RECTILINEAR_WIPE = 1

    def __init__(self, dimx=600, dimy=600, ren=None, renWin=None, iren=None, debug=True):
        '''creates the rendering pipeline'''
        # create a rendering window and renderer
        if ren == None:
            self.ren = vtk.vtkRenderer()
        else:
            self.ren = ren
        if renWin == None:
            self.renWin = vtk.vtkRenderWindow()
        else:
            self.renWin = renWin
        if iren == None:
            self.iren = vtk.vtkRenderWindowInteractor()
        else:
            self.iren = iren
        # holder for list of actors
        self.actors = {}
        self.debug = debug

        self.renWin.SetSize(dimx, dimy)
        self.renWin.AddRenderer(self.ren)

        self.style = CILInteractorStyle(self)
        self.style.debug = debug

        self.iren.SetInteractorStyle(self.style)
        self.iren.SetRenderWindow(self.renWin)
        self.iren.Initialize()
        self.ren.SetBackground(.1, .2, .4)

        self.camera = vtk.vtkCamera()
        self.camera.ParallelProjectionOn()
        self.flipCameraPosition = False
        self.ren.SetActiveCamera(self.camera)

        # data (input 1)
        self.img3D = None
        self.slicenos = [0, 0, 0]
        self.sliceOrientation = SLICE_ORIENTATION_XY
        self.axes_initialised = False
        #Actors
        self.voi = vtk.vtkExtractVOI()
        self.ia = vtk.vtkImageHistogramStatistics()
        self.iacursor = vtk.vtkImageHistogramStatistics()
        self.voicursor = vtk.vtkExtractVOI()
        #self.sliceActorNo = 0

        imageSlice = vtk.vtkImageSlice()
        imageSliceMapper = vtk.vtkImageSliceMapper()
        imageSlice.SetMapper(imageSliceMapper)
        imageSlice.GetProperty().SetInterpolationTypeToNearest()
        self.imageSlice = imageSlice
        self.imageSliceMapper = imageSliceMapper

        # input 2
        self.image2 = None
        self.voi2 = vtk.vtkExtractVOI()
        self.imageSlice2 = vtk.vtkImageSlice()
        self.imageSliceMapper2 = vtk.vtkImageSliceMapper()
        self.imageSlice2.SetMapper(self.imageSliceMapper2)

        # Help text
        self.helpActor = vtk.vtkActor2D()
        self.helpActor.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
        self.helpActor.GetPositionCoordinate().SetValue(0.1, 0.5)
        self.helpActor.VisibilityOff()
        # self.ren.AddActor(self.helpActor)
        self.AddActor(self.helpActor, HELP_ACTOR)

        #initial Window/Level
        self.InitialLevel = 0
        self.InitialWindow = 0

        #ViewerEvent
        self.event = ViewerEventManager()

        # ROI Widget
        self.ROIWidget = vtk.vtkBoxWidget()
        self.ROIWidget.SetInteractor(self.iren)
        self.ROIWidget.HandlesOn()
        self.ROIWidget.TranslationEnabledOn()
        self.ROIWidget.RotationEnabledOff()
        self.ROIWidget.GetOutlineProperty().SetColor(0, 1, 0)
        self.ROIWidget.OutlineCursorWiresOff()
        self.ROIWidget.SetPlaceFactor(1)
        self.ROIWidget.KeyPressActivationOff()

        self.ROIWidget.AddObserver(vtk.vtkWidgetEvent.Select, self.style.OnROIModifiedEvent, 1.0)

        # edge points of the ROI
        self.ROI = ()

        # Edge points of Volumetric ROI
        self.ROIV = None

        #picker
        self.picker = vtk.vtkPropPicker()
        self.picker.PickFromListOn()
        self.picker.AddPickList(self.imageSlice)

        self.iren.SetPicker(self.picker)

        # corner annotation
        self.cornerAnnotation = vtk.vtkCornerAnnotation()
        self.cornerAnnotation.SetMaximumFontSize(12)
        self.cornerAnnotation.PickableOff()
        self.cornerAnnotation.VisibilityOff()
        self.cornerAnnotation.GetTextProperty().ShadowOn()
        self.cornerAnnotation.SetLayerNumber(1)

        #used to scale corner annotation and decide whether to interpolate:
        self.image_is_downsampled = False
        self.visualisation_downsampling = [1, 1, 1]
        self.display_unsampled_coords = False

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
        self.cursorActor.SetLayerNumber(0)
        self.cursorMapper.SetInputData(self.cursor.GetOutput())
        self.cursorActor.SetMapper(self.cursorMapper)
        # self.getRenderer().AddActor(self.cursorActor)
        self.AddActor(self.cursorActor, CURSOR_ACTOR)

        # Zoom
        self.InitialCameraPosition = ()

        # XY Plot actor for histogram
        self.displayHistogram = False
        self.firstHistogram = 0
        self.roiIA = vtk.vtkImageAccumulate()
        self.roiVOI = vtk.vtkExtractVOI()
        self.histogramPlotActor = vtk.vtkXYPlotActor()
        self.histogramPlotActor.ExchangeAxesOff()
        self.histogramPlotActor.SetXLabelFormat("%g")
        self.histogramPlotActor.SetXLabelFormat("%g")
        self.histogramPlotActor.SetAdjustXLabels(3)
        self.histogramPlotActor.SetXTitle("Level")
        self.histogramPlotActor.SetYTitle("N")
        self.histogramPlotActor.SetXValuesToValue()
        self.histogramPlotActor.SetPlotColor(0, (0, 1, 1))
        self.histogramPlotActor.SetPosition2(0.6, 0.6)
        self.histogramPlotActor.SetPosition(0.4, 0.4)

        # XY Plot for X and Y slices
        self.displayLinePlot = False
        self.linePlot = 0
        self.lineVOIX = vtk.vtkExtractVOI()
        self.lineVOIY = vtk.vtkExtractVOI()
        self.linePlotActor = vtk.vtkXYPlotActor()
        self.linePlotActor.ExchangeAxesOff()
        self.linePlotActor.SetXTitle("")
        self.linePlotActor.SetYTitle("")
        self.linePlotActor.SetXLabelFormat("%.1f")
        self.linePlotActor.SetYLabelFormat("%.1e")
        #self.linePlotActor.SetAdjustXLabels(3)
        #self.linePlotActor.SetXTitle( "Level" )
        #self.linePlotActor.SetYTitle( "N" )
        self.linePlotActor.SetXValuesToValue()
        self.linePlotActor.SetPlotColor(0, (1, 0, 0.5))
        self.linePlotActor.SetPlotColor(1, (1, 1, 0))
        self.linePlotActor.SetPosition(0, 0.1)
        self.linePlotActor.SetPosition2(1, 0.4)

        # Makes sure that x axis only goes as far as the number of pixels in the image
        self.linePlotActor.SetAdjustXLabels(0)

        # Add legend
        self.linePlotActor.SetPlotLabel(0, 'horiz')
        self.linePlotActor.SetPlotLabel(1, 'vert')
        self.linePlotActor.LegendOn()

        # crosshair lines for X Y slices
        self.horizLine = vtk.vtkLine()
        self.vertLine = vtk.vtkLine()
        self.crosshairsActor = vtk.vtkActor()
        # self.getRenderer().AddActor(self.crosshairsActor)
        self.AddActor(self.crosshairsActor, CROSSHAIR_ACTOR)

        # rescale input image
        # contains (scale, shift)
        self.rescale = [False, (1, 0)]

        # ImageTracer
        self.imageTracer = vtk.vtkImageTracerWidget()
        # set Interactor
        self.imageTracer.SetInteractor(self.iren)
        self.imageTracer.SetCaptureRadius(1.5)
        self.imageTracer.GetLineProperty().SetColor(0.8, 0.8, 1.0)
        self.imageTracer.GetLineProperty().SetLineWidth(3.0)
        self.imageTracer.GetHandleProperty().SetColor(0.4, 0.4, 1.0)
        self.imageTracer.GetSelectedHandleProperty().SetColor(1.0, 1.0, 1.0)
        # Set the size of the glyph handle
        self.imageTracer.GetGlyphSource().SetScale(2.0)
        # Set the initial rotation of the glyph if desired.  The default glyph
        # set internally by the widget is a '+' so rotating 45 deg. gives a 'x'
        self.imageTracer.GetGlyphSource().SetRotationAngle(45.0)
        self.imageTracer.GetGlyphSource().Modified()
        self.imageTracer.ProjectToPlaneOn()
        self.imageTracer.SetHandleLeftMouseButton(True)
        # Set autoclose to on
        self.imageTracer.AutoCloseOn()
        self.imageTracer.AddObserver(vtk.vtkWidgetEvent.Select, self.style.OnTracerModifiedEvent, 1.0)

        # axis orientation widget
        om = vtk.vtkAxesActor()
        ori = vtk.vtkOrientationMarkerWidget()
        ori.SetOutlineColor(0.9300, 0.5700, 0.1300)
        ori.SetInteractor(self.iren)
        ori.SetOrientationMarker(om)
        ori.SetViewport(0.0, 0.0, 0.4, 0.4)
        ori.SetEnabled(1)
        ori.InteractiveOff()
        self.orientation_marker = ori

        self.__vis_mode = CILViewer2D.IMAGE_WITH_OVERLAY
        self.setVisualisationToImageWithOverlay()

    def log(self, msg):
        if self.debug:
            print(msg)

    def getInteractor(self):
        return self.iren

    def getRenderer(self):
        return self.ren

    def setInput3DData(self, imageData):
        '''alias of setInputData, kept for backward compatibility'''
        return self.setInputData(imageData)

    def setInputData(self, imageData):
        self.log("setInputData")
        self.img3D = imageData
        self.installPipeline()
        self.axes_initialised = True

    def setInputData2(self, imageData):
        self.image2 = imageData
        # TODO resample on image1
        # print ("setInputData2")
        self.installPipeline2()
        
    def setInputAsNumpy(self, numpyarray,  origin=(0, 0, 0), spacing=(1., 1., 1.),
                        rescale=True, dtype=vtk.VTK_UNSIGNED_SHORT):
        self.rescale[0] = rescale

        importer = Converter.numpy2vtkImporter(numpyarray, spacing, origin)
        importer.Update()

        if rescale:
            # rescale to appropriate VTK_UNSIGNED_SHORT
            stats = vtk.vtkImageAccumulate()
            stats.SetInputData(importer.GetOutput())
            stats.Update()
            iMin = stats.GetMin()[0]
            iMax = stats.GetMax()[0]
            if (iMax - iMin == 0):
                scale = 1
            else:
                if dtype == vtk.VTK_UNSIGNED_SHORT:
                    scale = vtk.VTK_UNSIGNED_SHORT_MAX / (iMax - iMin)
                elif dtype == vtk.VTK_UNSIGNED_INT:
                    scale = vtk.VTK_UNSIGNED_INT_MAX / (iMax - iMin)

            self.rescale[1] = (scale, -iMin)
            shiftScaler = vtk.vtkImageShiftScale()
            shiftScaler.SetInputData(importer.GetOutput())
            shiftScaler.SetScale(scale)
            shiftScaler.SetShift(-iMin)
            shiftScaler.SetOutputScalarType(dtype)
            shiftScaler.Update()
            self.img3D = shiftScaler.GetOutput()
        else:
            self.img3D = importer.GetOutput()

        self.installPipeline()

    def displaySlice(self, sliceno= [0]):
        self.setActiveSlice(sliceno)
        self.updatePipeline()
        self.renWin.Render()

    def updatePipeline(self, resetcamera=False):
        if self.vis_mode == CILViewer2D.IMAGE_WITH_OVERLAY:
            self.updateImageWithOverlayPipeline(resetcamera=resetcamera)
        elif self.vis_mode == CILViewer2D.RECTILINEAR_WIPE:
            self.updateRectilinearWipePipeline(resetcamera=resetcamera)

        self.AdjustCamera(resetcamera)
        self.renWin.Render()

    def updateRectilinearWipePipeline(self, resetcamera=False):
        extent = self.updateMainVOI()
        self.voi.SetVOI(*extent)
        #TODO what happens if image2 has a different sampling?
        self.voi2.SetVOI(*extent)
        self.wipeSliceMapper.SetOrientation(self.sliceOrientation)

    def updateMainVOI(self):
        # get the current slice
        extent = [ i for i in self.img3D.GetExtent()]
        extent[self.sliceOrientation * 2] = self.getActiveSlice()
        extent[self.sliceOrientation * 2 + 1] = self.getActiveSlice()
        self.voi.SetVOI(extent[0], extent[1],
                   extent[2], extent[3],
                   extent[4], extent[5])
        self.log ("extent {0}".format(extent))
        self.voi.Update()
        self.log("VOI dimensions {0}".format(self.voi.GetOutput().GetDimensions()))
        return extent

    def updateImageWithOverlayPipeline(self, resetcamera=False):
        extent = self.updateMainVOI()
        self.ia.Update()
        self.imageSliceMapper.SetOrientation(self.sliceOrientation)
        self.imageSlice.Update()

        if self.image2 is not None:
            self.voi2.SetVOI(self.voi.GetVOI())
            self.imageSliceMapper2.SetOrientation(self.sliceOrientation)
            self.imageSlice2.Update()
            
        text = self.createAnnotationText("slice", (self.getActiveSlice(), self.img3D.GetDimensions()[self.sliceOrientation] - 1))
        self.updateCornerAnnotation(text, 0)

        if self.displayHistogram:
            self.updateROIHistogram()
        try:
            if not self.img3D is None:
                # print ("self.img3D" , self.img3D)
                # Set the tracer widget's projection normal to the current orientation
                self.imageTracer.SetProjectionNormal(self.sliceOrientation)
                # Set the Tracer widget's position along the current projection normal,
                # we want this on top of the image so it can be seen above all slices.
                # On the X and Z axes, slice 0 is at the top as the axis points into
                # the screen.
                slice_coords = [0, 0, 0]
                # When we are viewing the Y direction, the axis goes into the page
                # so we have to swap which end of the axis the tracer is placed so
                # that it isn't in the shadow of the slice.
                if self.GetSliceOrientation() == SLICE_ORIENTATION_XZ:
                    slice_coords[self.GetSliceOrientation()] = self.img3D.GetDimensions()[SLICE_ORIENTATION_XZ] - 1
                self.imageTracer.SetProjectionPosition(self.style.image2world(slice_coords)[self.GetSliceOrientation()])
            else:
                print("self.img3D None")
        except Exception as ge:
            print(ge)
        self.AdjustCamera(resetcamera)
        self.renWin.Render()

    @property
    def vis_mode(self):
        return self.__vis_mode

    @vis_mode.setter
    def vis_mode(self, value):
        if value in [CILViewer2D.IMAGE_WITH_OVERLAY, CILViewer2D.RECTILINEAR_WIPE]:
            self.__vis_mode = value

    def setVisualisationPipelineMethodTo(self, method):
        if self.img3D is None:
            return
        # get the current visualisation mode
        if self.vis_mode != method:
            # remove current pipeline
            self.uninstallPipeline()
            if self.image2 is not None:
                self.uninstallPipeline2()
            # install the new pipeline
            self.vis_mode = method
            self.installPipeline()

    def setVisualisationToImageWithOverlay(self):
        self.setVisualisationPipelineMethodTo(CILViewer2D.IMAGE_WITH_OVERLAY)

    def setVisualisationToRectilinearWipe(self):
        self.setVisualisationPipelineMethodTo(CILViewer2D.RECTILINEAR_WIPE)

    def installPipeline(self):
        if self.vis_mode == CILViewer2D.IMAGE_WITH_OVERLAY:
            if self.img3D is not None:
                self.installImageWithOverlayPipeline()
            if self.image2 is not None:
                self.installPipeline2()
        elif self.vis_mode == CILViewer2D.RECTILINEAR_WIPE:
            self.installRectilinearWipePipeline()

        self.ren.ResetCamera()
        self.ren.Render()

        self.camera.SetViewUp(0, -1, 0)

        if not self.axes_initialised:
            self.camera.Azimuth(180)

        self.AdjustCamera()

        self.ren.AddViewProp(self.cursorActor)
        self.cursorActor.VisibilityOn()

        self.iren.Initialize()
        self.renWin.Render()

    def installPipeline2(self):
        if self.image2 is not None:
            if self.vis_mode == CILViewer2D.IMAGE_WITH_OVERLAY:
                self.installImageWithOverlayPipeline2()
            elif self.vis_mode == CILViewer2D.RECTILINEAR_WIPE:
                pass
        else:
            self.log("installPipeline2 no data")

    def installImageWithOverlayPipeline(self):
        '''Slices a 3D volume and then creates an actor to be rendered'''
        self.log("installPipeline")
        self.ren.AddViewProp(self.cornerAnnotation)

        self.voi.SetInputData(self.img3D)
        #select one slice in Z
        extent = [ i for i in self.img3D.GetExtent()]
        for i in range(len(self.slicenos)):
            self.slicenos[i] = round((extent[i * 2+1] + extent[i * 2])/2)

        extent[self.sliceOrientation * 2] = self.getActiveSlice()
        extent[self.sliceOrientation * 2 + 1] = self.getActiveSlice()
        
        self.voi.SetVOI(extent[0], extent[1],
                extent[2], extent[3],
                extent[4], extent[5])

        self.voi.SetVOI(extent[0], extent[1], extent[2], extent[3], extent[4], extent[5])

        self.voi.Update()
        # set window/level for current slices
        self.ia.SetInputData(self.voi.GetOutput())
        self.ia.SetAutoRangePercentiles(5.0, 95.)
        self.ia.Update()
        cmin, cmax = self.ia.GetAutoRange()
        # set the level to the average between the percentiles
        level = (cmin + cmax) / 2
        # accomodates all values between the level an the percentiles
        window = (cmax - cmin) / 2

        self.InitialLevel = level
        self.InitialWindow = window
        self.log("level {0} window {1}".format(self.InitialLevel, self.InitialWindow))

        self.imageSliceMapper.SetInputConnection(self.voi.GetOutputPort())

        self.imageSlice.GetProperty().SetColorLevel(self.InitialLevel)
        self.imageSlice.GetProperty().SetColorWindow(self.InitialWindow)

        if self.image_is_downsampled:
            self.imageSlice.GetProperty().SetInterpolationTypeToLinear()
        else:
            self.imageSlice.GetProperty().SetInterpolationTypeToNearest()

        self.imageSlice.Update()

        self.imageTracer.SetProjectionPosition(self.style.image2world([0,0,0])[self.GetSliceOrientation()])
        
        self.AddActor(self.imageSlice, SLICE_ACTOR)

        self.imageTracer.SetViewProp(self.imageSlice)

    def installImageWithOverlayPipeline2(self):
        '''Slices a 3D volume and then creates an actor to be rendered'''
        self.log("installPipeline2")
        if self.image2 is not None:
            # render image2
            self.voi2.SetVOI(self.voi.GetVOI())
            self.voi2.SetInputData(self.image2)
            self.voi2.Update()
            lut = vtk.vtkLookupTable()

            ai = vtk.vtkImageHistogramStatistics()
            ai.SetInputConnection(self.voi2.GetOutputPort())
            ai.Update()

            self.lut2 = lut
            lut.SetNumberOfColors(7)
            lut.SetHueRange(.4, .6)
            lut.SetSaturationRange(1, 1)
            lut.SetValueRange(0.7, 0.7)
            lut.SetAlphaRange(0, 0.5)
            lut.Build()

            cov = vtk.vtkImageMapToColors()
            self.image2map = cov
            cov.SetInputConnection(self.voi2.GetOutputPort())
            cov.SetLookupTable(lut)
            cov.Update()

            self.imageSliceMapper2.SetInputConnection(cov.GetOutputPort())
            self.imageSlice2.Update()
            self.AddActor(self.imageSlice2, OVERLAY_ACTOR)
            self.ren.ResetCamera()
            self.ren.Render()

            self.AdjustCamera()

            self.iren.Initialize()
            self.renWin.Render()
        else:
            print ("installPipeline2 no data")

    def installRectilinearWipePipeline(self):
        '''Create the pipeline for the rectilinear wipe'''
        self.log("installRectilinearWipePipeline")
        extent1 = list(self.img3D.GetExtent())
        #extent is slice number N
        for i in range(len(self.slicenos)):
            self.slicenos[i] = round((extent1[i * 2+1] + extent1[i * 2])/2)
        active_slice_num = self.getActiveSlice()
        orient = self.GetSliceOrientation()
        extent1[orient]   = active_slice_num
        extent1[orient+1] = active_slice_num
        extent2 = extent1[:]

        self.voi.SetVOI(*extent1)
        self.voi2.SetVOI(*extent2)

        wipe = vtk.vtkImageRectilinearWipe()
        wipeSliceMapper = vtk.vtkImageSliceMapper()
        wipeSlice = vtk.vtkImageSlice()

        wipe.SetInputConnection(0, self.voi.GetOutputPort())
        wipe.SetInputConnection(1, self.voi2.GetOutputPort())
        # should set the position to center of viewport
        wipe.SetPosition(10, 10)
        wipe.SetWipe(0)

        wipeSliceMapper.SetInputConnection(wipe.GetOutputPort())
        wipeSliceMapper.SetOrientation(orient)

        wipeSlice.SetMapper(wipeSliceMapper)
        wipeSlice.GetProperty().SetInterpolationTypeToNearest()
        wipeSlice.GetProperty().SetColorLevel(self.InitialLevel)
        wipeSlice.GetProperty().SetColorWindow(self.InitialWindow)
        wipeSlice.Update()

        self.wipe = wipe
        self.wipeSliceMapper = wipeSliceMapper
        self.wipeActor = wipeSlice

        self.AddActor(wipeSlice, WIPE_ACTOR)

    def AdjustCamera(self, resetcamera=False):
        self.ren.ResetCameraClippingRange()

        # adjust camera focal point
        camera = self.getRenderer().GetActiveCamera()
        fp = list(camera.GetFocalPoint())
        pos = list(camera.GetPosition())
        if self.flipCameraPosition:
            fp[self.sliceOrientation] = -self.getActiveSlice()
            pos[self.sliceOrientation] = - pos[self.sliceOrientation]
            self.flipCameraPosition = False
            # have to reset to false so it doesn't flip when we scroll.
        else:
            fp[self.sliceOrientation] = self.getActiveSlice()
        
        camera.SetFocalPoint(fp)
        camera.SetPosition(pos)

        if resetcamera:
            self.ren.ResetCamera()

    def getROI(self):
        return self.ROI

    def getROIExtent(self):
        p0 = self.ROI[0]
        p1 = self.ROI[1]
        return (p0[0], p1[0], p0[1], p1[1], p0[2], p1[2])

    ############### Handle events are moved to the interactor style

    def GetRenderWindow(self):
        return self.renWin

    def startRenderLoop(self):
        self.iren.Start()

    def setSliceOrientation(self, axis):
        if axis in ['x', 'y', 'z']:
            self.getInteractor().SetKeyCode(axis)
            self.style.OnKeyPress(self.getInteractor(), "KeyPressEvent")

    def GetSliceOrientation(self):
        return self.sliceOrientation

    def setActiveSlice(self, sliceno):
        self.slicenos[self.GetSliceOrientation()] = sliceno

    def getActiveSlice(self):
        return self.slicenos[self.GetSliceOrientation()]

    def setVisualisationDownsampling(self, value):
        self.visualisation_downsampling = value
        if value != [1, 1, 1]:
            self.image_is_downsampled = True
            self.imageSlice.GetProperty().SetInterpolationTypeToLinear()
        else:
            self.image_is_downsampled = False
            self.imageSlice.GetProperty().SetInterpolationTypeToNearest()

    def getVisualisationDownsampling(self):
        return self.visualisation_downsampling

    def setDisplayUnsampledCoordinates(self, value):
        self.display_unsampled_coords = value

    def getDisplayUnsampledCoordinates(self):
        return self.display_unsampled_coords

    def updateCornerAnnotation(self, text, idx=0, visibility=True):
        if visibility:
            self.cornerAnnotation.VisibilityOn()
        else:
            self.cornerAnnotation.VisibilityOff()

        self.cornerAnnotation.SetText(idx, text)
        self.iren.Render()

    def createAnnotationText(self, display_type, data):
        ''' Returns string to be set as the corner annotation, giving
        the coordinates or slice number (may be downsampled or unsampled coordinates)

        Args:
            display_type (str) :    'slice', 'pick', 'roi' - determines the
                                    way in which the data is displayed
            data (tuple):           the data to be displayed.'''

        text = None

        if isinstance(data, tuple):

            if display_type == "slice":
                if self.display_unsampled_coords and self.image_is_downsampled:
                    # Different method for converting to world coords, as we only
                    # have coordinates in one direction
                    data = list(data)
                    slice_coord = [0, 0, 0]
                    axis_length = [0, 0, 0]
                    slice_coord[self.GetSliceOrientation()] = data[0]
                    axis_length[self.GetSliceOrientation()] = data[1] + 1
                    slice_coord = self.style.image2world(slice_coord)[self.GetSliceOrientation()]
                    axis_length = self.style.image2world(axis_length)[self.GetSliceOrientation()] - 1
                    data = (round(slice_coord), round(axis_length))
                text = "Slice %d/%d" % data

            else:
                # In all other cases, we have coordinates, and then we have an extra value
                # The extra value shouldn't be converted in the same way
                # TODO: check whether we need some kind of conversion on these 'extra' values
                if self.display_unsampled_coords and self.image_is_downsampled:
                    data = list(data)
                    extra_info = data.pop(-1)
                    data = self.style.image2world(data)
                    data.append(extra_info)
                    # Round the coordinates to integers:
                    # Without rounding the %d formatting
                    # later on just truncates to integer
                    for i, d in enumerate(data):
                        if i < 3:
                            data[i] = round(d)
                    data = tuple(data)

            if display_type == "pick":
                text = "[%d,%d,%d] : %.2g" % data

            elif display_type == "roi":
                text = "ROI: %d x %d x %d, %.2f kp" % data

        return text

    def saveRender(self, filename, renWin=None):
        '''Save the render window to PNG file'''
        # screenshot code:

        if renWin == None:
            renWin = self.renWin
        SaveRenderToPNG(self.renWin, filename)

    def validateValue(self, value, axis):
        dims = self.img3D.GetDimensions()
        max_slice = [x - 1 for x in dims]

        axis_int = {'x': 0, 'y': 1, 'z': 2}

        if axis in axis_int.keys():
            i = axis_int[axis]
        else:
            raise KeyError

        if value < 0:
            return 0
        if value > max_slice[i]:
            return max_slice[i]
        else:
            return value

    def updateROIHistogram(self):
        self.log("Updating hist")

        extent = [0 for i in range(6)]
        if self.GetSliceOrientation() == SLICE_ORIENTATION_XY:
            self.log("slice orientation : XY")
            extent[0] = self.validateValue(min(self.ROI[0][0], self.ROI[1][0]), 'x')
            extent[1] = self.validateValue(max(self.ROI[0][0], self.ROI[1][0]), 'x')
            extent[2] = self.validateValue(min(self.ROI[0][1], self.ROI[1][1]), 'y')
            extent[3] = self.validateValue(max(self.ROI[0][1], self.ROI[1][1]), 'y')
            extent[4] = self.getActiveSlice()
            extent[5] = self.getActiveSlice()
            # y = abs(roi[1][1] - roi[0][1])
        elif self.GetSliceOrientation() == SLICE_ORIENTATION_XZ:
            self.log("slice orientation : XZ")
            extent[0] = self.validateValue(min(self.ROI[0][0], self.ROI[1][0]), 'x')
            extent[1] = self.validateValue(max(self.ROI[0][0], self.ROI[1][0]), 'x')
            # x = abs(roi[1][0] - roi[0][0])
            extent[4] = self.validateValue(min(self.ROI[0][2], self.ROI[1][2]), 'z')
            extent[5] = self.validateValue(max(self.ROI[0][2], self.ROI[1][2]), 'z')
            # y = abs(roi[1][2] - roi[0][2])
            extent[2] = self.getActiveSlice()
            extent[3] = self.getActiveSlice()
        elif self.GetSliceOrientation() == SLICE_ORIENTATION_YZ:
            self.log("slice orientation : YZ")
            extent[2] = self.validateValue(min(self.ROI[0][1], self.ROI[1][1]), 'y')
            extent[3] = self.validateValue(max(self.ROI[0][1], self.ROI[1][1]), 'y')
            # x = abs(roi[1][1] - roi[0][1])
            extent[4] = self.validateValue(min(self.ROI[0][2], self.ROI[1][2]), 'z')
            extent[5] = self.validateValue(max(self.ROI[0][2], self.ROI[1][2]), 'z')
            # y = abs(roi[1][2] - roi[0][2])
            extent[0] = self.getActiveSlice()
            extent[1] = self.getActiveSlice()

        self.log("updateROIHistogram {0}".format(extent))
        self.roiVOI.SetVOI(extent)
        self.roiVOI.SetInputData(self.img3D)
        self.roiVOI.Update()
        irange = self.roiVOI.GetOutput().GetScalarRange()

        self.roiIA.SetInputData(self.roiVOI.GetOutput())

        self.roiIA.IgnoreZeroOff()
        self.roiIA.SetComponentOrigin(int(irange[0]), 0, 0)
        self.roiIA.SetComponentSpacing(1, 0, 0)
        self.roiIA.Update()

        #use 255 bins
        delta = self.roiIA.GetMax()[0] - self.roiIA.GetMin()[0]
        nbins = 255
        self.roiIA.SetComponentSpacing(delta / nbins, 0, 0)
        self.roiIA.SetComponentExtent(0, nbins, 0, 0, 0, 0)
        self.roiIA.Update()

        self.histogramPlotActor.AddDataSetInputConnection(self.roiIA.GetOutputPort())
        self.histogramPlotActor.SetXRange(irange[0], irange[1])
        self.histogramPlotActor.SetYRange(self.roiIA.GetOutput().GetScalarRange())

    def setColorWindowLevel(self, window, level):
        self.imageSlice.GetProperty().SetColorLevel(level)
        self.imageSlice.GetProperty().SetColorWindow(window)
        self.imageSlice.Update()
        self.ren.Render()
        self.renWin.Render()

    def setColorWindow(self, window):
        self.imageSlice.GetProperty().SetColorWindow(window)
        self.imageSlice.Update()
        self.ren.Render()
        self.renWin.Render()

    def setColorLevel(self, level):
        self.imageSlice.GetProperty().SetColorLevel(level)
        self.imageSlice.Update()
        self.ren.Render()
        self.renWin.Render()

    def updateLinePlot(self, imagecoordinate, display):

        self.displayLinePlot = display
        extent_x = list(self.img3D.GetExtent())
        extent_y = list(self.img3D.GetExtent())
        self.log("imagecoordinate {0}".format(imagecoordinate))

        if display:
            #extract profile along X
            if self.GetSliceOrientation() == SLICE_ORIENTATION_XY:
                self.log("slice orientation : XY")
                extent_y[0] = imagecoordinate[0]
                extent_y[1] = imagecoordinate[0]

                extent_x[2] = imagecoordinate[1]
                extent_x[3] = imagecoordinate[1]

                extent_y[4] = self.getActiveSlice()
                extent_y[5] = self.getActiveSlice()
                extent_x[4] = self.getActiveSlice()
                extent_x[5] = self.getActiveSlice()

                self.linePlotActor.SetDataObjectXComponent(0, 0)
                self.linePlotActor.SetDataObjectXComponent(1, 1)

                #y = abs(roi[1][1] - roi[0][1])
            elif self.GetSliceOrientation() == SLICE_ORIENTATION_XZ:
                self.log("slice orientation : XZ")
                extent_y[0] = imagecoordinate[0]
                extent_y[1] = imagecoordinate[0]
                #x = abs(roi[1][0] - roi[0][0])
                extent_x[4] = imagecoordinate[2]
                extent_x[5] = imagecoordinate[2]
                #y = abs(roi[1][2] - roi[0][2])
                extent_x[2] = self.getActiveSlice()
                extent_x[3] = self.getActiveSlice()
                extent_y[2] = self.getActiveSlice()
                extent_y[3] = self.getActiveSlice()
                self.linePlotActor.SetDataObjectXComponent(0,0)
                self.linePlotActor.SetDataObjectXComponent(1,2)

            elif self.GetSliceOrientation() == SLICE_ORIENTATION_YZ:
                self.log("slice orientation : YZ")
                extent_y[2] = imagecoordinate[1]
                extent_y[3] = imagecoordinate[1]
                #x = abs(roi[1][1] - roi[0][1])
                extent_x[4] = imagecoordinate[2]
                extent_x[5] = imagecoordinate[2]
                #y = abs(roi[1][2] - roi[0][2])
                extent_x[0] = self.getActiveSlice()
                extent_x[1] = self.getActiveSlice()
                extent_y[0] = self.getActiveSlice()
                extent_y[1] = self.getActiveSlice()

                self.linePlotActor.SetDataObjectXComponent(0, 1)
                self.linePlotActor.SetDataObjectXComponent(1, 2)

            self.log("x {0} extent_x {1}".format(imagecoordinate[0], extent_x))
            self.log("y {0} extent_y {1}".format(imagecoordinate[1], extent_y))
            self.lineVOIX.SetVOI(extent_x)
            self.lineVOIX.SetInputData(self.img3D)
            self.lineVOIX.Update()
            self.lineVOIY.SetVOI(extent_y)
            self.lineVOIY.SetInputData(self.img3D)
            self.lineVOIY.Update()

            # fill
            if self.linePlot == 0:
                self.linePlotActor.AddDataSetInputConnection(self.lineVOIX.GetOutputPort())
                self.linePlotActor.AddDataSetInputConnection(self.lineVOIY.GetOutputPort())
                # self.getRenderer().AddActor(self.linePlotActor)
                self.AddActor(self.linePlotActor, LINEPLOT_ACTOR)
                self.linePlot = 1

            # Set position of line plot

            # Set up character sizes and borders
            width = 8
            border = 12
            height = 12

            # Calculate the world origin in display coordinates
            origin_display = self.style.world2display((0, 0, 0))

            # Calculate the offset due to labels and borders on the graphs y-axis
            max_y = max(int(self.lineVOIY.GetOutput().GetScalarRange()[1]),
                        int(self.lineVOIX.GetOutput().GetScalarRange()[1]))
            y_digits = len(str(max_y))
            x_min_offset = (width * y_digits) + border
            y_min_offset = height + border

            # Offset the origin to account for the labels
            origin_nview = self.style.display2normalisedViewport(
                (origin_display[0] - x_min_offset, origin_display[1] - y_min_offset))

            # Calculate the far right border
            top_right_disp = self.style.world2display(self.style.GetImageWorldExtent())
            top_right_nview = self.style.display2normalisedViewport(
                (top_right_disp[0] + border + height, top_right_disp[1]))

            # Set the position on the image
            self.linePlotActor.SetPosition(origin_nview)
            self.linePlotActor.SetPosition2(top_right_nview[0] - origin_nview[0], 0.4)

            self.log("data length x {0} y {1}".format(self.lineVOIX.GetOutput().GetDimensions(),
                                                      self.lineVOIY.GetOutput().GetDimensions()))
            self.linePlotActor.VisibilityOn()
            self.crosshairsActor.VisibilityOn()

            self.renWin.Render()

        else:
            self.linePlotActor.VisibilityOff()
            self.crosshairsActor.VisibilityOff()

            self.renWin.Render()

    def getColourWindow(self):
        return self.imageSlice.GetProperty().GetColorWindow()

    def getColourLevel(self):
        return self.imageSlice.GetProperty().GetColorLevel()

    def AddActor(self, actor, name=None):
        '''print("ADDING ACTOR", name)
        self.log("Calling AddActor " + name)
        present_actors = self.ren.GetActors() # Only seems to return some of the actors - possibly only the visible ones?
        present_actors.InitTraversal()
        self.log("Currently present actors {}".format(present_actors))

        print("Current len", present_actors.GetNumberOfItems())
    
        for i in range(present_actors.GetNumberOfItems()):
            nextActor = present_actors.GetNextActor()
            nextActor.SetVisibility(False)
            self.log("{} {} Visibility {}".format(i, nextActor, nextActor.GetVisibility() ))
            self.log("ClassName"+ str( nextActor.GetClassName()))

        
        print("intermediate len", self.ren.GetActors().GetNumberOfItems())        
        if name is None:
            name = 'actor_{}'.format(present_actors.GetNumberOfItems()+1)'''

        self.ren.AddActor(actor)
        self.actors[name]  = actor

    def GetActorsDict(self):
        return self.actors

    def GetActor(self, name):
        if name in self.actors:
            actor = self.actors[name]
            return actor
        else:
            return (None)

    def uninstallPipeline(self):
        '''uninstall the current visualisation pipeline'''
        if self.vis_mode == CILViewer2D.IMAGE_WITH_OVERLAY:
            self.removeActor([SLICE_ACTOR, HISTOGRAM_ACTOR])
        elif self.vis_mode == CILViewer2D.RECTILINEAR_WIPE:
            self.removeActor(WIPE_ACTOR)

    def removeActor(self, actor):
        '''remove named actor'''
        if not isinstance(actor, (list, tuple)):
            actor = [actor]
        keys = self.actors.keys()
        for a in actor:
            if a in keys:
                self.ren.RemoveActor(self.actors[a])
                self.actors.pop(a)

    def uninstallPipeline2(self):
        if self.vis_mode == CILViewer2D.IMAGE_WITH_OVERLAY:
            self.removeActor(OVERLAY_ACTOR)
        elif self.vis_mode == CILViewer2D.RECTILINEAR_WIPE:
            # rectilinear wipe visualises 2 images in the same pipeline
            pass

    def getSliceMapWindow(self, percentiles):
        ia = vtk.vtkImageHistogramStatistics()
        ia.SetInputData(self.img3D)
        ia.Update()
        ia.SetAutoRangePercentiles(*percentiles)
        ia.Update()
        min, max = ia.GetAutoRange()
        return min, max

    def getSliceColorWindow(self):
        return self.imageSlice.GetProperty().GetColorWindow()

    def getSliceColorLevel(self):
        return self.imageSlice.GetProperty().GetColorLevel()
