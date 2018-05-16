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
from vtk.util import numpy_support , vtkImageImportFromArray
from enum import Enum
import os
import math

SLICE_ORIENTATION_XY = 2 # Z
SLICE_ORIENTATION_XZ = 1 # Y
SLICE_ORIENTATION_YZ = 0 # X

CONTROL_KEY = 8
SHIFT_KEY = 4
ALT_KEY = -128


# Converter class
class Converter():

    # Utility functions to transform numpy arrays to vtkImageData and viceversa
    @staticmethod
    def numpy2vtkImporter(nparray, spacing=(1.,1.,1.), origin=(0,0,0)):
        '''Creates a vtkImageImportFromArray object and returns it.
        
        It handles the different axis order from numpy to VTK'''
        importer = vtkImageImportFromArray.vtkImageImportFromArray()
        importer.SetArray(numpy.transpose(nparray, [2,1,0]).copy())
        importer.SetDataSpacing(spacing)
        importer.SetDataOrigin(origin)
        return importer

    @staticmethod
    def vtk2numpy(imgdata, transpose=[0,1,2]):
        '''Converts the VTK data to 3D numpy array

        Points in a VTK ImageData have indices as X-Y-Z (FORTRAN-contiguos)
        index = x + dimX * y + z * dimX * dimY,
        meaning that the slicing a VTK ImageData is easy in the Z axis

        Points in Numpy have indices as Z-Y-X (C-contiguous)
        index = z + dimZ * y + x * dimZ * dimY
        meaning that the slicing of a numpy array is easy on the X axis

        The function imgdata.GetPointData().GetScalars() returns a pointer to a
        vtk<TYPE>Array where the data is stored as X-Y-Z.
        '''
        img_data = numpy_support.vtk_to_numpy(
                imgdata.GetPointData().GetScalars())

        dims = imgdata.GetDimensions()
        print ("vtk2numpy: VTKImageData dims {0}".format(dims))

        old = True
        if old:
            dims = (dims[2],dims[1],dims[0])
            data3d = numpy.reshape(img_data, dims, order='C')
            data3d = numpy.ascontiguousarray(data3d)
        else:
            data3d = numpy.ascontiguousarray(
                numpy.reshape(img_data, dims, order='F')
                )
            data3d = numpy.transpose(data3d, [2,1,0])
        if transpose == [0,1,2]:
            return data3d
        else:
            return numpy.transpose(data3d, transpose).copy()


    @staticmethod
    def tiffStack2numpy(filename=None, indices=None,
                        extent = None , sampleRate = None ,
                        flatField = None, darkField = None
                        , filenames= None, tiffOrientation=1):
        '''Converts a stack of TIFF files to numpy array.
        
        filename must contain the whole path. The filename is supposed to be named and
        have a suffix with the ordinal file number, i.e. /path/to/projection_%03d.tif
        
        indices are the suffix, generally an increasing number
        
        Optionally extracts only a selection of the 2D images and (optionally)
        normalizes.
        '''
        if filename is not None and indices is not None:
            filenames = [ filename % num for num in indices]
        return Converter._tiffStack2numpy(filenames=filenames, extent=extent,
                                         sampleRate=sampleRate,
                                         flatField=flatField,
                                         darkField=darkField)
    @staticmethod
    def tiffStack2numpyEnforceBounds(filename=None, indices=None,
                        extent = None , sampleRate = None ,
                        flatField = None, darkField = None
                        , filenames= None, tiffOrientation=1, bounds=(512,512,512)):
        """
        Converts a stack of TIFF files to numpy array. This is constrained to a 512x512x512 cube

        filename must contain the whole path. The filename is supposed to be named and
        have a suffix with the ordinal file number, i.e. /path/to/projection_%03d.tif

        indices are the suffix, generally an increasing number

        Optionally extracts only a selection of the 2D images and (optionally)
        normalizes.

        :param (string) filename:   full path prefix
        :param (list)   indices:    Indices to append to path for file selection
        :param (tuple)  extent:     Allows option to select a subset
        :param (tuple)  sampleRate: Allows downsampling to reduce data load on visualiser
        :param          flatField:  --
        :param          darkField:  --
        :param (list)   filenames:  Filenames for processing
        :param (int)    tiffOrientation: --
        :param (tuple)  bounds:     Maximum size of display cube (x,y,z)

        :return (numpy.ndarray): Image data as a numpy array
        """

        if filename is not None and indices is not None:
            filenames = [filename % num for num in indices]

        # Get number of files as an index value
        file_index = len(filenames) - 1

        # Get the xy extent of the first image in the list
        if extent is None:
            reader = vtk.vtkTIFFReader()
            reader.SetFileName(filenames[0])
            reader.SetOrientationType(tiffOrientation)
            reader.Update()
            img_ext = reader.GetOutput().GetExtent()

            stack_extent =  img_ext[0:5] + (file_index,)
            size = stack_extent[1::2]
        else:
            size = extent[1::2]

        # Calculate re-sample rate
        sample_rate = tuple(map(lambda x,y: math.ceil(float(x)/y), size, bounds))

        # If a user has defined resample rate, check to see which has higher factor and keep that
        if sampleRate is not None:
            sampleRate = Converter.highest_tuple_element(sampleRate, sample_rate)
        else:
            sampleRate = sample_rate

        # Re-sample input filelist
        list_sample_index = sampleRate[2]
        filenames = filenames[::list_sample_index]

        return Converter._tiffStack2numpy(filenames=filenames, extent=extent,
                                          sampleRate=sampleRate,
                                          flatField=flatField,
                                          darkField=darkField)


    @staticmethod
    def _tiffStack2numpy(filenames,
                        extent = None , sampleRate = None ,\
                        flatField = None, darkField = None, tiffOrientation=1):
        '''Converts a stack of TIFF files to numpy array.
        
        filename must contain the whole path. The filename is supposed to be named and
        have a suffix with the ordinal file number, i.e. /path/to/projection_%03d.tif
        
        indices are the suffix, generally an increasing number
        
        Optionally extracts only a selection of the 2D images and (optionally)
        normalizes.
        '''

        stack = vtk.vtkImageData()
        reader = vtk.vtkTIFFReader()
        voi = vtk.vtkExtractVOI()

        stack_image = numpy.asarray([])
        nreduced = len(filenames)

        for num in range(len(filenames)):


            #fn = filename % indices[num]
            fn = filenames[num]
            print ("resampling %s" % ( fn ) )
            reader.SetFileName(fn)
            reader.SetOrientationType(tiffOrientation)
            reader.Update()
            print (reader.GetOutput().GetScalarTypeAsString())
            if num == 0:

                # Extent
                if extent is None:
                    sliced = reader.GetOutput().GetExtent()
                    stack.SetExtent(sliced[0],sliced[1], sliced[2],sliced[3], 0, nreduced-1)

                    if sampleRate is not None:
                        voi.SetSampleRate(sampleRate)
                        ext = numpy.asarray([(sliced[2*i+1] - sliced[2*i])/sampleRate[i] for i in range(3)], dtype=int)
                        stack.SetExtent(0, ext[0], 0, ext[1], 0, nreduced - 1)
                else:
                    sliced = extent
                    voi.SetVOI(extent)

                    # Sample Rate
                    if sampleRate is not None:
                        voi.SetSampleRate(sampleRate)
                        ext = numpy.asarray([(sliced[2*i+1] - sliced[2*i])/sampleRate[i] for i in range(3)], dtype=int)
                        # print ("ext {0}".format(ext))
                        stack.SetExtent(0, ext[0] , 0, ext[1], 0, nreduced-1)
                    else:
                         stack.SetExtent(0, sliced[1] - sliced[0], 0, sliced[3]-sliced[2], 0, nreduced-1)

                # Flatfield
                if (flatField != None and darkField != None):
                    stack.AllocateScalars(vtk.VTK_FLOAT, 1)
                else:
                    stack.AllocateScalars(reader.GetOutput().GetScalarType(), 1)



                print ("Image Size: %d" % ((sliced[1]+1)*(sliced[3]+1) ))
                stack_image = Converter.vtk2numpy(stack)
                print ("Stack shape %s" % str(numpy.shape(stack_image)))

            if extent is not None or sampleRate is not None :
                voi.SetInputData(reader.GetOutput())
                voi.Update()
                img = voi.GetOutput()
            else:
                img = reader.GetOutput()

            theSlice = Converter.vtk2numpy(img)[0]
            if darkField != None and flatField != None:
                print("Try to normalize")
                #if numpy.shape(darkField) == numpy.shape(flatField) and numpy.shape(flatField) == numpy.shape(theSlice):
                theSlice = Converter.normalize(theSlice, darkField, flatField, 0.01)
                print (theSlice.dtype)


            print ("Slice shape %s" % str(numpy.shape(theSlice)))
            stack_image[num] = theSlice.copy()

        return stack_image

    @staticmethod
    def normalize(projection, dark, flat, def_val=0):
        a = (projection - dark)
        b = (flat-dark)
        with numpy.errstate(divide='ignore', invalid='ignore'):
            c = numpy.true_divide( a, b )
            c[ ~ numpy.isfinite( c )] = def_val  # set to not zero if 0/0
        return c

    @staticmethod
    def highest_tuple_element(user,calc):
        """
        Returns a tuple containing the maximum combination in elementwise comparison
        :param (tuple)  user: User suppliec tuple
        :param (tuple)  calc: Calculated tuple

        :return (tuple): Highest elementwise combination
        """

        output = []
        for u, c in zip(user,calc):
            if u > c:
                output.append(u)
            else:
                output.append(c)

        return tuple(output)





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


class CILInteractorStyle(vtk.vtkInteractorStyleImage):

    def __init__(self, callback):
        vtk.vtkInteractorStyleImage.__init__(self)
        self.callback = callback
        self._viewer = callback
        priority = 1.0
        self.debug = True

        self.AddObserver("MouseWheelForwardEvent" , self.OnMouseWheelForward , priority)
        self.AddObserver("MouseWheelBackwardEvent" , self.OnMouseWheelBackward, priority)
        self.AddObserver('KeyPressEvent', self.OnKeyPress, priority)
        self.AddObserver('LeftButtonPressEvent',
                         self.OnLeftButtonPressEvent,
                         priority)
        self.AddObserver('RightButtonPressEvent', self.OnRightButtonPressEvent, priority)
        self.AddObserver('LeftButtonReleaseEvent', self.OnLeftButtonReleaseEvent, priority)
        self.AddObserver('RightButtonReleaseEvent', self.OnRightButtonReleaseEvent, priority)
        self.AddObserver('MouseMoveEvent', self.OnMouseMoveEvent, priority)

        self.InitialEventPosition = (0,0)

        # Initialise difference from zoom event start point
        self.dy = 0

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
        x,y = self.GetInteractor().GetEventPosition()
        return (x - self.InitialEventPosition[0] , y - self.InitialEventPosition[1])

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
        return self._viewer.sliceno

    def SetActiveSlice(self, sliceno):
        self._viewer.sliceno = sliceno

    def UpdatePipeline(self, reset = False):
        self._viewer.updatePipeline(reset)

    def GetActiveCamera(self):
        return self._viewer.ren.GetActiveCamera()

    def SetActiveCamera(self, camera):
        self._viewer.ren.SetActiveCamera(camera)

    def ResetCamera(self):
        self._viewer.ren.ResetCamera()

    def Render(self):
        self._viewer.renWin.Render()

    def UpdateSliceActor(self):
        self._viewer.sliceActor.Update()

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

    def GetWindowLevel(self):
        return self._viewer.wl

    def SetROI(self, roi):
        self._viewer.ROI = roi

    def GetROI(self):
        return self._viewer.ROI

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
        axis_dict = {
            "x": 0,
            "y": 1,
            "z": 2
        }
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
        world_image_min = (0,0,0)

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
            box_pos[3] = self._truncateBox(box_pos[2], world_image_max,"y")
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
        maxSlice = self.GetDimensions()[self.GetSliceOrientation()]
        shift = interactor.GetShiftKey()
        advance = 1
        if shift:
            advance = 10

        if (self.GetActiveSlice() + advance < maxSlice):
            self.SetActiveSlice(self.GetActiveSlice() + advance)

            self.UpdatePipeline()
        else:
            self.log ("maxSlice %d request %d" % (maxSlice, self.GetActiveSlice() ))

        if self.GetViewerEvent("SHOW_LINE_PROFILE_EVENT"):
            self.DisplayLineProfile(interactor, event, True)

    def OnMouseWheelBackward(self, interactor, event):
        minSlice = 0
        shift = interactor.GetShiftKey()
        advance = 1
        if shift:
            advance = 10
        if (self.GetActiveSlice() - advance >= minSlice):
            self.SetActiveSlice( self.GetActiveSlice() - advance)
            self.UpdatePipeline()
        else:
            self.log ("minSlice %d request %d" % (minSlice, self.GetActiveSlice() ))
        if self.GetViewerEvent("SHOW_LINE_PROFILE_EVENT"):
            self.DisplayLineProfile(interactor, event, True)

    def OnKeyPress(self, interactor, event):

        print ("Pressed key %s" % interactor)
        # Slice Orientation
        if interactor.GetKeyCode() == "X":
            # slice on the other orientation

            self.SetSliceOrientation ( SLICE_ORIENTATION_YZ )
            self.SetActiveSlice( int(self.GetDimensions()[0] / 2) )
            self.UpdatePipeline(True)

        elif interactor.GetKeyCode() == "Y":
            # slice on the other orientation
            self.SetSliceOrientation (  SLICE_ORIENTATION_XZ )
            self.SetActiveSlice ( int(self.GetInputData().GetDimensions()[1] / 2) )
            self.UpdatePipeline(True)

        elif interactor.GetKeyCode() == "Z":
            # slice on the other orientation
            self.SetSliceOrientation (  SLICE_ORIENTATION_XY )
            self.SetActiveSlice ( int(self.GetInputData().GetDimensions()[2] / 2) )
            self.UpdatePipeline(True)

        if interactor.GetKeyCode() == "x":
            # Change the camera view point
            camera = vtk.vtkCamera()
            camera.ParallelProjectionOn()
            camera.SetFocalPoint(self.GetActiveCamera().GetFocalPoint())
            camera.SetViewUp(self.GetActiveCamera().GetViewUp())
            newposition = [i for i in self.GetActiveCamera().GetFocalPoint()]
            newposition[SLICE_ORIENTATION_YZ] = numpy.sqrt(newposition[SLICE_ORIENTATION_XY] ** 2 + newposition[SLICE_ORIENTATION_XZ] ** 2)
            camera.SetPosition(newposition)
            camera.SetViewUp(0,0,1) # Orig
            self.SetActiveCamera(camera)
            self.Render()
            interactor.SetKeyCode("X")
            self.OnKeyPress(interactor, event)

        elif interactor.GetKeyCode() == "y":
             # Change the camera view point
            camera = vtk.vtkCamera()
            camera.ParallelProjectionOn()
            camera.SetFocalPoint(self.GetActiveCamera().GetFocalPoint())
            camera.SetViewUp(self.GetActiveCamera().GetViewUp())
            newposition = [i for i in self.GetActiveCamera().GetFocalPoint()]
            newposition[SLICE_ORIENTATION_XZ] = numpy.sqrt(newposition[SLICE_ORIENTATION_XY] ** 2 + newposition[SLICE_ORIENTATION_YZ] ** 2)

            # Invert Y position to ensure graph axis are consistent with expectation.
            newposition[1] = -newposition[1]
            camera.SetPosition(newposition)
            camera.SetViewUp(0,0,1) # Orig
            # camera.SetViewUp(0,0,1)
            self.SetActiveCamera(camera)
            self.Render()
            interactor.SetKeyCode("Y")
            self.OnKeyPress(interactor, event)

        elif interactor.GetKeyCode() == "z":
             # Change the camera view point
            camera = vtk.vtkCamera()
            camera.ParallelProjectionOn()
            camera.SetFocalPoint(self.GetActiveCamera().GetFocalPoint())
            camera.SetViewUp(self.GetActiveCamera().GetViewUp())
            newposition = [i for i in self.GetActiveCamera().GetFocalPoint()]
            newposition[SLICE_ORIENTATION_XY] = numpy.sqrt(newposition[SLICE_ORIENTATION_YZ] ** 2 + newposition[SLICE_ORIENTATION_XZ] ** 2)
            camera.SetPosition(newposition)
            camera.SetViewUp(0,1,0)
            self.SetActiveCamera(camera)
            self.ResetCamera()
            self.Render()
            interactor.SetKeyCode("Z")
            self.OnKeyPress(interactor, event)

        elif interactor.GetKeyCode() == "a":
            # reset color/window
            cmin, cmax = self._viewer.ia.GetAutoRange()

            # probably the level could be the median of the image within
            # the percintiles
            level = self._viewer.ia.GetMedian()
            # accommodates all values between the level an the percentiles
            window = 2*max(abs(level-cmin),abs(level-cmax))

            self.SetInitialLevel( level )
            self.SetInitialWindow( window  )

            self.GetWindowLevel().SetLevel(self.GetInitialLevel())
            self.GetWindowLevel().SetWindow(self.GetInitialWindow())

            self.GetWindowLevel().Update()

            self.UpdateSliceActor()
            self.AdjustCamera()
            self.Render()

        elif interactor.GetKeyCode() == "s":
            filename = "current_render"
            self.SaveRender(filename)

        elif interactor.GetKeyCode() == "q":
            print ("Render loop terminating by pressing %s" % (interactor.GetKeyCode(), ))
            interactor.SetKeyCode("e")
            self.OnKeyPress(interactor, event)

        elif interactor.GetKeyCode() == "l":
            if self.GetViewerEvent("SHOW_LINE_PROFILE_EVENT"):

                self.SetEventInactive("SHOW_LINE_PROFILE_EVENT")
                self.DisplayLineProfile(interactor, event, False)
            else:
                self.SetEventActive("SHOW_LINE_PROFILE_EVENT")
                self.DisplayLineProfile(interactor, event, True)

        else :
            #print ("Unhandled event %s" % (interactor.GetKeyCode(), )))
            pass

    def OnLeftButtonPressEvent(self, interactor, event):
        # print ("INTERACTOR", interactor)
        # interactor = self._viewer.GetInteractor()

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
            self.log ("Event %s is CREATE_ROI_EVENT" % (event))

        elif alt and not (shift and ctrl):
            self.SetEventActive("DELETE_ROI_EVENT")
            self.GetROIWidget().Off()
            self._viewer.updateCornerAnnotation("", 1, False)
            self.SetDisplayHistogram(False)
            self.Render()
            self.log ("Event %s is DELETE_ROI_EVENT" % (event))

        elif not (ctrl and alt and shift):
            self.SetEventActive("PICK_EVENT")
            self.HandlePickEvent(interactor, event)
            self.log ("Event %s is PICK_EVENT" % (event))

    def SetDisplayHistogram(self, display):
        if display:
            if (self._viewer.displayHistogram == 0):
                self.GetRenderer().AddActor(self._viewer.histogramPlotActor)
                self.firstHistogram = 1
                self.Render()

            self._viewer.histogramPlotActor.VisibilityOn()
            self._viewer.displayHistogram = True
        else:
            self._viewer.histogramPlotActor.VisibilityOff()
            self._viewer.displayHistogram = False

    def OnLeftButtonReleaseEvent(self, interactor, event):
        interactor = self._viewer.GetInteractor()

        if self.GetViewerEvent("CREATE_ROI_EVENT"):
            self.OnROIModifiedEvent(interactor, event)

        elif self.GetViewerEvent("PICK_EVENT"):
            self.HandlePickEvent(interactor, event)

        # Turn off CREATE_ROI and PICK_EVENT
        self.SetEventInactive("CREATE_ROI_EVENT")
        self.SetEventInactive("PICK_EVENT")
        self.SetEventInactive("DELETE_ROI_EVENT")

    def OnRightButtonPressEvent(self, interactor, event):
        interactor = self._viewer.GetInteractor()

        alt = interactor.GetAltKey()
        shift = interactor.GetShiftKey()
        ctrl = interactor.GetControlKey()

        self.SetInitialEventPosition(interactor.GetEventPosition())


        if alt and not (ctrl and shift):
            self.SetEventActive("WINDOW_LEVEL_EVENT")
            self.log ("Event %s is WINDOW_LEVEL_EVENT" % (event))
            self.HandleWindowLevel(interactor, event)
        elif shift and not (ctrl and alt):
            self.SetEventActive("ZOOM_EVENT")
            self.SetInitialCameraPosition( self.GetActiveCamera().GetPosition())
            self.log ("Event %s is ZOOM_EVENT" % (event))
        elif ctrl and not (shift and alt):
            self.SetEventActive("PAN_EVENT")
            self.SetInitialCameraPosition ( self.GetActiveCamera().GetPosition() )
            self.log ("Event %s is PAN_EVENT" % (event))

    def OnRightButtonReleaseEvent(self, interactor, event):
        self.log (event)
        if self.GetViewerEvent("WINDOW_LEVEL_EVENT"):
            self.SetInitialLevel( self.GetWindowLevel().GetLevel() )
            self.SetInitialWindow ( self.GetWindowLevel().GetWindow() )
        elif self.GetViewerEvent("ZOOM_EVENT") or self.GetViewerEvent("PAN_EVENT"):
            self.SetInitialCameraPosition( () )

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
        self.SetROI((vox1 , vox2))
        roi = self.GetROI()

        # Debug messages
        self.log("ROI {0}".format(roi))
        self.log ("Pixel1 %d,%d,%d Value %f" % vox1 )
        self.log ("Pixel2 %d,%d,%d Value %f" % vox2 )

        # Calculate the size of the ROI
        if self.GetSliceOrientation() == SLICE_ORIENTATION_XY:
            self.log ("slice orientation : XY")
            x = abs(roi[1][0] - roi[0][0])
            y = abs(roi[1][1] - roi[0][1])
            z = abs(roi[1][2] - roi[0][2])

        elif self.GetSliceOrientation() == SLICE_ORIENTATION_XZ:
            self.log ("slice orientation : XZ")
            x = abs(roi[1][0] - roi[0][0])
            y = abs(roi[1][2] - roi[0][2])
            z = abs(roi[1][1] - roi[0][1])

        elif self.GetSliceOrientation() == SLICE_ORIENTATION_YZ:
            self.log ("slice orientation : YZ")
            x = abs(roi[1][1] - roi[0][1])
            y = abs(roi[1][2] - roi[0][2])
            z = abs(roi[1][1] - roi[0][1])

        # Update the text bottom right of the viewer and histogram
        text = "ROI: %d x %d x %d, %.2f kp" % (x,y,z,float(x*y)/1024.)
        self.log (text)
        self.UpdateCornerAnnotation(text, 1)
        self.UpdateROIHistogram()
        # self.SetViewerEvent( ViewerEvent.NO_EVENT )
        self.SetEventInactive("CREATE_ROI_EVENT")

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


    def display2imageCoordinate(self, viewerposition):
        """
        Convert display coordinates into image coordinates and add the pixel value

        :param viewerposition: (x,y) position of the selected point in the display window
        :return: (x,y,z,a) x,y,z index of the selected slice + a, the pixel value
        """
        vc = vtk.vtkCoordinate()
        vc.SetCoordinateSystemToViewport()
        vc.SetValue(viewerposition[0:2] + (0.0,))

        pickPosition = list(vc.GetComputedWorldValue(self.GetRenderer()))
        # print ("PICK POS", pickPosition)

        pickPosition[self.GetSliceOrientation()] = \
            self.GetInputData().GetSpacing()[self.GetSliceOrientation()] * self.GetActiveSlice() + \
            self.GetInputData().GetOrigin()[self.GetSliceOrientation()]
        self.log ("Pick Position " + str (pickPosition))

        if (pickPosition != [0,0,0]):

            imagePosition = self.world2imageCoordinate(pickPosition)

            pixelValue = self.GetInputData().GetScalarComponentAsDouble(
                    imagePosition[0], imagePosition[1], imagePosition[2], 0)
            if self._viewer.rescale[0]:
                scale , shift = self._viewer.rescale[1]
                # pix = orig * scale + shift
                # orig = (-shift + pix) / scale
                pixelValue = (-shift + pixelValue) / scale
            return (
                self.validateValue(imagePosition[0], 'x'),
                self.validateValue(imagePosition[1], 'y'),
                self.validateValue(imagePosition[2], 'z'),
                pixelValue
            )
        else:
            return (0,0,0,0)

    def createVox(self, world_coordinates):

        # Translate the world coordinates to an image index
        imagePosition = self.world2imageCoordinate(world_coordinates)

        pixelValue = self.GetInputData().GetScalarComponentAsDouble(
            imagePosition[0], imagePosition[1], imagePosition[2], 0)
        if self._viewer.rescale[0]:
            scale, shift = self._viewer.rescale[1]
            pixelValue = (-shift + pixelValue) / scale
        return (
            self.validateValue(imagePosition[0], 'x'),
            self.validateValue(imagePosition[1], 'y'),
            self.validateValue(imagePosition[2], 'z'),
            pixelValue
        )

    def world2imageCoordinate(self, world_coordinates):
        """
        Convert from the world or global coordinates to image coordinates
        :param world_coordinates: (x,y,z)
        :return: (x,y,z) in image coorindates eg. slice index
        """

        dims = self.GetInputData().GetDimensions()
        self.log(dims)
        spac = self.GetInputData().GetSpacing()
        orig = self.GetInputData().GetOrigin()

        return [round(world_coordinates[i] / spac[i] + orig[i]) for i in range(3)]

    def image2world(self, image_coordinates):

        spac = self.GetInputData().GetSpacing()
        orig = self.GetInputData().GetOrigin()

        return [(image_coordinates[i] - orig[i]) * spac[i] for i in range(3)]

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

    def display2normalisedViewport(self,display_coords):

        wsize = self.GetRenderWindow().GetSize()

        x = display_coords[0]/wsize[0]
        y = display_coords[1]/wsize[1]

        return x,y


##################################  END ######################################

    def OnMouseMoveEvent(self, interactor, event):

        if self.GetViewerEvent("WINDOW_LEVEL_EVENT"):
            self.log ("Event %s is WINDOW_LEVEL_EVENT" % (event))
            self.HandleWindowLevel(interactor, event)

        elif self.GetViewerEvent("PICK_EVENT"):
            self.HandlePickEvent(interactor, event)

        elif self.GetViewerEvent("ZOOM_EVENT"):
            self.HandleZoomEvent(interactor, event)

        elif self.GetViewerEvent("PAN_EVENT"):
            self.HandlePanEvent(interactor, event)

        elif self.GetViewerEvent("SHOW_LINE_PROFILE_EVENT"):
            self.DisplayLineProfile(interactor, event, True)


    def HandleZoomEvent(self, interactor, event):
        camera = self.GetActiveCamera()

        # Extract change from start of event
        dx,dy = interactor.GetDeltaEventPosition()
        window_y_size = self.GetRenderWindow().GetSize()[1]

        # Determine whether the user is zooming in or out
        change = dy - self.dy

        # Make sure that a change has been registered
        if change != 0:
            # >1 zoom in, <1 zoom out
            camera.Zoom(1 + change/window_y_size)
            self.Render()

        # Set the overall change value
        self.dy = dy

    def HandlePanEvent(self, interactor, event):

        x,y = interactor.GetEventPosition()
        x0,y0 = interactor.GetInitialEventPosition()

        ic = self.display2imageCoordinate((x,y))
        ic0 = self.display2imageCoordinate((x0,y0))

        dx = 1 * ( ic[0] - ic0[0] )
        dy = 1 * ( ic[1] - ic0[1] )

        camera = self.GetActiveCamera()
        newposition = [i for i in self.GetInitialCameraPosition()]
        newfocalpoint = [i for i in self.GetActiveCamera().GetFocalPoint()]
        if self.GetSliceOrientation() == SLICE_ORIENTATION_XY:
            newposition[0] -= dx
            newposition[1] -= dy
            newfocalpoint[0] = newposition[0]
            newfocalpoint[1] = newposition[1]
        elif self.GetSliceOrientation() == SLICE_ORIENTATION_XZ:
            newposition[0] -= dx
            newposition[2] -= dy
            newfocalpoint[0] = newposition[0]
            newfocalpoint[2] = newposition[2]
        elif self.GetSliceOrientation() == SLICE_ORIENTATION_YZ:
            newposition[1] -= dx
            newposition[2] -= dy
            newfocalpoint[2] = newposition[2]
            newfocalpoint[1] = newposition[1]
        camera.SetFocalPoint(newfocalpoint)
        camera.SetPosition(newposition)

        self.Render()

    def HandleWindowLevel(self, interactor, event):
        dx,dy = interactor.GetDeltaEventPosition()
        self.log ("Event delta %d %d" % (dx,dy))
        size = self.GetRenderWindow().GetSize()

        dx = 1 * dx / size[0]
        dy = 1 * dy / size[1]
        window = self.GetInitialWindow()
        level = self.GetInitialLevel()

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
        newWindow = window + dx
        newLevel  = level + dy

        # Stay away from zero and really small numbers
        if abs(newWindow) < 0.01:
            newWindow = 0.01 * (lambda x: -1 if x <0 else 1)(newWindow)

        if abs(newLevel) < 0.01:
            newLevel = 0.01 * (lambda x: -1 if x <0 else 1)(newLevel)

        self.GetWindowLevel().SetWindow(newWindow)
        self.GetWindowLevel().SetLevel(newLevel)
        self.log("new level {0} window {1}".format(newLevel,newWindow))
        self.GetWindowLevel().Update()
        self.UpdateSliceActor()
        self.AdjustCamera()

        self.Render()

    def HandlePickEvent(self, interactor, event):
        position = interactor.GetEventPosition()

        vox = self.display2imageCoordinate(position)
        # print ("Pixel %d,%d,%d Value %f" % vox )
        self._viewer.cornerAnnotation.VisibilityOn()
        self.UpdateCornerAnnotation("[%d,%d,%d] : %.2g" % vox , 0)
        self.Render()

    def DisplayLineProfile(self, interactor, event, display):
        x,y = interactor.GetEventPosition()
        ic = self.display2imageCoordinate((x,y))
        self.UpdateLinePlot(ic, display)

        # Plot horiz and vertical lines to indicate where the user is looking

        # Get the actor and line objects
        actor, vertLine, horizLine = self.GetCrosshairs()

        # Create the polydata where we will store all the geometric data
        linesPolyData = vtk.vtkPolyData()

        # Get the maximum extent of the image in the world
        world_image_max = self.GetImageWorldExtent()
        event_world = self.display2world((x,y))

        # Make sure that the crosshairs stop at the boundary of the image
        event_truncated = [0,0,0]

        for i,axis in enumerate(event_world):
            if axis > world_image_max[i]:
                event_truncated[i] = world_image_max[i]
            elif axis < 0:
                event_truncated[i] = 0.0
            else:
                event_truncated[i] = axis

        event_world = event_truncated

        # Set the end points of the lines
        if self.GetSliceOrientation() == SLICE_ORIENTATION_XY: #Z
            # Z Max +1 to make sure line is drawn on top
            top_of_world = world_image_max[2] + 1

            # Get line position from event postion in world coordinates
            horiz = event_world[0]
            vert = event_world[1]

            # X Line
            p0 = [horiz, 0.0, top_of_world]
            p1 = [horiz, world_image_max[1], top_of_world]

            # Y Line
            p2 = [0.0, vert, top_of_world]
            p3 = [world_image_max[0], vert, top_of_world]

        elif self.GetSliceOrientation() == SLICE_ORIENTATION_XZ: #Y
            # Camera is opposite side in this orientation so we use bottom of world, -1
            # Get line position from event postion in world coordinates
            horiz = event_world[0]
            vert = event_world[2]

            # X Line
            p0 = [horiz, -1, 0.0]
            p1 = [horiz, -1, world_image_max[2]]

            # Z Line
            p2 = [0.0, -1, vert]
            p3 = [world_image_max[0], -1, vert]

        elif self.GetSliceOrientation() == SLICE_ORIENTATION_YZ: #X
            # X Max +1 to make sure line is drawn on top
            top_of_world = world_image_max[0] + 1

            # Get line position from event postion in world coordinates
            horiz = event_world[1]
            vert = event_world[2]

            # Y Line
            p0 = [top_of_world, horiz, 0.0]
            p1 = [top_of_world, horiz, world_image_max[2]]

            # Z Line
            p2 = [top_of_world, 0.0, vert]
            p3 = [top_of_world, world_image_max[1], vert]

        # Create a vtkPoints container and store the points in it
        pts = vtk.vtkPoints()
        pts.InsertNextPoint(p0)
        pts.InsertNextPoint(p1)
        pts.InsertNextPoint(p2)
        pts.InsertNextPoint(p3)

        # Add the points to the polydata container
        linesPolyData.SetPoints(pts)

        # Create the first line (between Origin and P0)
        vertLine.GetPointIds().SetId(0, 0)  # the second 0 is the index of the Origin in linesPolyData's points
        vertLine.GetPointIds().SetId(1, 1)  # the second 1 is the index of P0 in linesPolyData's points

        # Create the second line (between Origin and P1)
        horizLine.GetPointIds().SetId(0, 2)  # the second 0 is the index of the Origin in linesPolyData's points
        horizLine.GetPointIds().SetId(1, 3)  # 2 is the index of P1 in linesPolyData's points

        # Create a vtkCellArray container and store the lines in it
        lines = vtk.vtkCellArray()
        lines.InsertNextCell(vertLine)
        lines.InsertNextCell(horizLine)

        # Add the lines to the polydata container
        linesPolyData.SetLines(lines)

        namedColors = vtk.vtkNamedColors()

        # Create a vtkUnsignedCharArray container and store the colors in it
        colors = vtk.vtkUnsignedCharArray()
        colors.SetNumberOfComponents(3)

        colors.InsertNextTypedTuple(namedColors.GetColor3ub("Yellow"))
        colors.InsertNextTypedTuple(namedColors.GetColor3ub("Magenta"))

        # Color the lines.
        # SetScalars() automatically associates the values in the data array passed as parameter
        # to the elements in the same indices of the cell data array on which it is called.
        linesPolyData.GetCellData().SetScalars(colors)

        # Setup the visualization pipeline
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(linesPolyData)

        actor.SetMapper(mapper)
        actor.GetProperty().SetLineWidth(2)

        self.UpdatePipeline()
        self.Render()

###############################################################################



class CILViewer2D():
    '''Simple Interactive Viewer based on VTK classes'''

    def __init__(self, dimx=600,dimy=600, ren=None, renWin=None,iren=None, debug=True):
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

        self.debug = debug

        self.renWin.SetSize(dimx,dimy)
        self.renWin.AddRenderer(self.ren)

        self.style = CILInteractorStyle(self)
        self.style.debug = debug

        self.iren.SetInteractorStyle(self.style)
        self.iren.SetRenderWindow(self.renWin)
        self.iren.Initialize()
        self.ren.SetBackground(.1, .2, .4)

        self.camera = vtk.vtkCamera()
        self.camera.ParallelProjectionOn()
        self.ren.SetActiveCamera(self.camera)

        # data
        self.img3D = None
        self.sliceno = 0
        self.sliceOrientation = SLICE_ORIENTATION_XY

        #Actors
        self.sliceActor = vtk.vtkImageActor()
        self.voi = vtk.vtkExtractVOI()
        self.wl = vtk.vtkImageMapToWindowLevelColors()
        self.ia = vtk.vtkImageHistogramStatistics()
        self.sliceActorNo = 0

        #initial Window/Level
        self.InitialLevel = 0
        self.InitialWindow = 0

        #ViewerEvent
        self.event = ViewerEventManager()

        # ROI Widget
        # self.ROIWidget = vtk.vtkBorderWidget()
        # self.ROIWidget.SetInteractor(self.iren)
        # self.ROIWidget.CreateDefaultRepresentation()
        # self.ROIWidget.GetBorderRepresentation().GetBorderProperty().SetColor(0,1,0)
        # self.ROIWidget.AddObserver(vtk.vtkWidgetEvent.Select, self.style.OnROIModifiedEvent, 1.0)

        self.ROIWidget = vtk.vtkBoxWidget()
        self.ROIWidget.SetInteractor(self.iren)
        self.ROIWidget.HandlesOn()
        self.ROIWidget.TranslationEnabledOn()
        self.ROIWidget.RotationEnabledOff()
        self.ROIWidget.GetOutlineProperty().SetColor(0,1,0)
        self.ROIWidget.OutlineCursorWiresOff()
        self.ROIWidget.SetPlaceFactor(1)

        # self.ROIWidget.SetInputConnection(self.img3D.GetOutput())
        self.ROIWidget.AddObserver(vtk.vtkWidgetEvent.Select, self.style.OnROIModifiedEvent, 1.0)

        # edge points of the ROI
        self.ROI = ()

        # Edge points of Volumetric ROI
        # self.ROIV = vtk.vtkExtractVOI()
        self.ROIV = None


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

        # Zoom
        self.InitialCameraPosition = ()

        # XY Plot actor for histogram
        self.displayHistogram = False
        self.firstHistogram = 0
        self.roiIA = vtk.vtkImageAccumulate()
        self.roiVOI = vtk.vtkExtractVOI()
        self.histogramPlotActor = vtk.vtkXYPlotActor()
        self.histogramPlotActor.ExchangeAxesOff();
        self.histogramPlotActor.SetXLabelFormat( "%g" )
        self.histogramPlotActor.SetXLabelFormat( "%g" )
        self.histogramPlotActor.SetAdjustXLabels(3)
        self.histogramPlotActor.SetXTitle( "Level" )
        self.histogramPlotActor.SetYTitle( "N" )
        self.histogramPlotActor.SetXValuesToValue()
        self.histogramPlotActor.SetPlotColor(0, (0,1,1) )
        self.histogramPlotActor.SetPosition2(0.6,0.6)
        self.histogramPlotActor.SetPosition(0.4,0.4)

        # XY Plot for X and Y slices
        self.displayLinePlot = False
        self.linePlot = 0
        self.lineVOIX = vtk.vtkExtractVOI()
        self.lineVOIY = vtk.vtkExtractVOI()
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
        self.linePlotActor.SetPlotColor(0, (1,0,0.5) )
        self.linePlotActor.SetPlotColor(1, (1,1,0) )
        self.linePlotActor.SetPosition(0,0.1)
        self.linePlotActor.SetPosition2(1,0.4)

        # Makes sure that x axis only goes as far as the number of pixels in the image
        self.linePlotActor.SetAdjustXLabels(0)

        # Add legend
        self.linePlotActor.SetPlotLabel(0,'horiz')
        self.linePlotActor.SetPlotLabel(1,'vert')
        self.linePlotActor.LegendOn()

        # crosshair lines for X Y slices
        self.horizLine = vtk.vtkLine()
        self.vertLine = vtk.vtkLine()
        self.crosshairsActor = vtk.vtkActor()
        self.GetRenderer().AddActor(self.crosshairsActor)

        # rescale input image
        # contains (scale, shift)
        self.rescale = [ False , (1,0) ]


    def log(self, msg):
        if self.debug:
            print(msg)

    def GetInteractor(self):
        return self.iren

    def GetRenderer(self):
        return self.ren

    def setInput3DData(self, imageData):
        self.img3D = imageData
        self.installPipeline()

    def setInputAsNumpy(self, numpyarray,  origin=(0,0,0), spacing=(1.,1.,1.),
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
            shiftScaler = vtk.vtkImageShiftScale ()
            shiftScaler.SetInputData(importer.GetOutput())
            shiftScaler.SetScale(scale)
            shiftScaler.SetShift(-iMin)
            shiftScaler.SetOutputScalarType(dtype)
            shiftScaler.Update()
            self.img3D = shiftScaler.GetOutput()
        else:
            self.img3D = importer.GetOutput()

        self.installPipeline()

    def displaySlice(self, sliceno = 0):
        self.sliceno = sliceno

        self.updatePipeline()

        self.renWin.Render()

        return self.sliceActorNo

    def updatePipeline(self, resetcamera = False):
        extent = [ i for i in self.img3D.GetExtent()]
        extent[self.sliceOrientation * 2] = self.sliceno
        extent[self.sliceOrientation * 2 + 1] = self.sliceno
        self.voi.SetVOI(extent[0], extent[1],
                   extent[2], extent[3],
                   extent[4], extent[5])
        self.log ("extent {0}".format(extent))
        self.voi.Update()
        self.log("VOI dimensions {0}".format(self.voi.GetOutput().GetDimensions()))
        self.ia.Update()
        self.wl.Update()
        self.sliceActor.SetDisplayExtent(extent[0], extent[1],
                   extent[2], extent[3],
                   extent[4], extent[5])
        self.sliceActor.Update()

        self.updateCornerAnnotation("Slice %d/%d" % (self.sliceno + 1 , self.img3D.GetDimensions()[self.sliceOrientation]))

        if self.displayHistogram:
            self.updateROIHistogram()

        self.AdjustCamera(resetcamera)

        self.renWin.Render()


    def installPipeline(self):
        '''Slices a 3D volume and then creates an actor to be rendered'''

        self.ren.AddViewProp(self.cornerAnnotation)

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
        self.ia.SetAutoRangePercentiles(1.0,99.)
        self.ia.Update()
        #cmax = self.ia.GetMax()[0]
        #cmin = self.ia.GetMin()[0]
        cmin, cmax = self.ia.GetAutoRange()
        # probably the level could be the median of the image within
        # the percentiles 
        level = self.ia.GetMedian()
        # accomodates all values between the level an the percentiles
        window = 2*max(abs(level-cmin),abs(level-cmax))

        self.InitialLevel = level
        self.InitialWindow = window
        self.log("level {0} window {1}".format(self.InitialLevel,
                                               self.InitialWindow))


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

        self.AdjustCamera()

        self.ren.AddViewProp(self.cursorActor)
        self.cursorActor.VisibilityOn()

        self.iren.Initialize()
        self.renWin.Render()
        #self.iren.Start()

    def AdjustCamera(self, resetcamera = False):
        self.ren.ResetCameraClippingRange()

        # adjust camera focal point
        camera = self.GetRenderer().GetActiveCamera()
        fp = list (camera.GetFocalPoint())
        fp[self.sliceOrientation] = self.sliceno
        camera.SetFocalPoint(fp)

        if resetcamera:
            self.ren.ResetCamera()


    def getROI(self):
        return self.ROI

    def getROIExtent(self):
        p0 = self.ROI[0]
        p1 = self.ROI[1]
        return (p0[0], p1[0],p0[1],p1[1],p0[2],p1[2])

    ############### Handle events are moved to the interactor style

    def GetRenderWindow(self):
        return self.renWin


    def startRenderLoop(self):
        self.iren.Start()

    def GetSliceOrientation(self):
        return self.sliceOrientation

    def GetActiveSlice(self):
        return self.sliceno

    def updateCornerAnnotation(self, text , idx=0, visibility=True):
        if visibility:
            self.cornerAnnotation.VisibilityOn()
        else:
            self.cornerAnnotation.VisibilityOff()

        self.cornerAnnotation.SetText(idx, text)
        self.iren.Render()

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

    def validateValue(self,value, axis):
        dims = self.img3D.GetDimensions()
        max_slice = [x-1 for x in dims]

        axis_int = {
            'x': 0,
            'y': 1,
            'z': 2
        }

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
        print ("Updating hist")

        extent = [0 for i in range(6)]
        if self.GetSliceOrientation() == SLICE_ORIENTATION_XY:
            self.log("slice orientation : XY")
            extent[0] = self.validateValue(min(self.ROI[0][0], self.ROI[1][0]), 'x')
            extent[1] = self.validateValue(max(self.ROI[0][0], self.ROI[1][0]), 'x')
            extent[2] = self.validateValue(min(self.ROI[0][1], self.ROI[1][1]), 'y')
            extent[3] = self.validateValue(max(self.ROI[0][1], self.ROI[1][1]), 'y')
            extent[4] = self.GetActiveSlice()
            extent[5] = self.GetActiveSlice()
            # y = abs(roi[1][1] - roi[0][1])
        elif self.GetSliceOrientation() == SLICE_ORIENTATION_XZ:
            self.log("slice orientation : XZ")
            extent[0] = self.validateValue(min(self.ROI[0][0], self.ROI[1][0]), 'x')
            extent[1] = self.validateValue(max(self.ROI[0][0], self.ROI[1][0]), 'x')
            # x = abs(roi[1][0] - roi[0][0])
            extent[4] = self.validateValue(min(self.ROI[0][2], self.ROI[1][2]), 'z')
            extent[5] = self.validateValue(max(self.ROI[0][2], self.ROI[1][2]), 'z')
            # y = abs(roi[1][2] - roi[0][2])
            extent[2] = self.GetActiveSlice()
            extent[3] = self.GetActiveSlice()
        elif self.GetSliceOrientation() == SLICE_ORIENTATION_YZ:
            self.log("slice orientation : YZ")
            extent[2] = self.validateValue(min(self.ROI[0][1], self.ROI[1][1]), 'y')
            extent[3] = self.validateValue(max(self.ROI[0][1], self.ROI[1][1]), 'y')
            # x = abs(roi[1][1] - roi[0][1])
            extent[4] = self.validateValue(min(self.ROI[0][2], self.ROI[1][2]), 'z')
            extent[5] = self.validateValue(max(self.ROI[0][2], self.ROI[1][2]), 'z')
            # y = abs(roi[1][2] - roi[0][2])
            extent[0] = self.GetActiveSlice()
            extent[1] = self.GetActiveSlice()

        self.log("updateROIHistogram {0}".format(extent))
        self.roiVOI.SetVOI(extent)
        self.roiVOI.SetInputData(self.img3D)
        self.roiVOI.Update()
        irange = self.roiVOI.GetOutput().GetScalarRange()

        self.roiIA.SetInputData(self.roiVOI.GetOutput())

        self.roiIA.IgnoreZeroOff()
        self.roiIA.SetComponentOrigin( int(irange[0]),0,0 );
        self.roiIA.SetComponentSpacing( 1,0,0 );
        self.roiIA.Update()

        #use 255 bins
        delta = self.roiIA.GetMax()[0] - self.roiIA.GetMin()[0]
        nbins = 255
        self.roiIA.SetComponentSpacing(delta/nbins,0,0)
        self.roiIA.SetComponentExtent(0,nbins,0,0,0,0 )
        self.roiIA.Update()

        self.histogramPlotActor.AddDataSetInputConnection(self.roiIA.GetOutputPort())
        self.histogramPlotActor.SetXRange(irange[0],irange[1])
        self.histogramPlotActor.SetYRange( self.roiIA.GetOutput().GetScalarRange() )

    def setSliceOrientation(self, axis):
        if axis in ['x','y','z']:
            self.GetInteractor().SetKeyCode(axis)
            self.style.OnKeyPress(self.GetInteractor(), "KeyPressEvent")

    def updateLinePlot(self, imagecoordinate, display):

        self.displayLinePlot = display
        extent_x = list(self.img3D.GetExtent())
        extent_y = list(self.img3D.GetExtent())
        self.log("imagecoordinate {0}".format(imagecoordinate))

        if display:
            #extract profile along X
            if self.GetSliceOrientation() == SLICE_ORIENTATION_XY:
                self.log ("slice orientation : XY")
                extent_y[0] = imagecoordinate[0]
                extent_y[1] = imagecoordinate[0]

                extent_x[2] = imagecoordinate[1]
                extent_x[3] = imagecoordinate[1]

                extent_y[4] = self.GetActiveSlice()
                extent_y[5] = self.GetActiveSlice()
                extent_x[4] = self.GetActiveSlice()
                extent_x[5] = self.GetActiveSlice()

                self.linePlotActor.SetDataObjectXComponent(0,0)
                self.linePlotActor.SetDataObjectXComponent(1,1)

                #y = abs(roi[1][1] - roi[0][1])
            elif self.GetSliceOrientation() == SLICE_ORIENTATION_XZ:
                self.log ("slice orientation : XZ")
                extent_y[0] = imagecoordinate[0]
                extent_y[1] = imagecoordinate[0]
                #x = abs(roi[1][0] - roi[0][0])
                extent_x[4] = imagecoordinate[2]
                extent_x[5] = imagecoordinate[2]
                #y = abs(roi[1][2] - roi[0][2])
                extent_x[2] = self.GetActiveSlice()
                extent_x[3] = self.GetActiveSlice()
                extent_y[2] = self.GetActiveSlice()
                extent_y[3] = self.GetActiveSlice()
                self.linePlotActor.SetDataObjectXComponent(0,0)
                self.linePlotActor.SetDataObjectXComponent(1,2)


            elif self.GetSliceOrientation() == SLICE_ORIENTATION_YZ:
                self.log ("slice orientation : YZ")
                extent_y[2] = imagecoordinate[1]
                extent_y[3] = imagecoordinate[1]
                #x = abs(roi[1][1] - roi[0][1])
                extent_x[4] = imagecoordinate[2]
                extent_x[5] = imagecoordinate[2]
                #y = abs(roi[1][2] - roi[0][2])
                extent_x[0] = self.GetActiveSlice()
                extent_x[1] = self.GetActiveSlice()
                extent_y[0] = self.GetActiveSlice()
                extent_y[1] = self.GetActiveSlice()

                self.linePlotActor.SetDataObjectXComponent(0,1)
                self.linePlotActor.SetDataObjectXComponent(1,2)


            self.log("x {0} extent_x {1}".format(imagecoordinate[0], extent_x) )
            self.log("y {0} extent_y {1}".format(imagecoordinate[1], extent_y) )
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
                self.GetRenderer().AddActor(self.linePlotActor)
                self.linePlot = 1


            # Set position of line plot

            # Set up character sizes and borders
            width = 8
            border = 12
            height = 12

            # Calculate the world origin in display coordinates
            origin_display = self.style.world2display((0,0,0))

            # Calculate the offset due to labels and borders on the graphs y-axis
            max_y = max(
                int(self.lineVOIY.GetOutput().GetScalarRange()[1]),
                int(self.lineVOIX.GetOutput().GetScalarRange()[1])
            )
            y_digits = len(str(max_y))
            x_min_offset = (width * y_digits) + border
            y_min_offset = height + border

            # Offset the origin to account for the labels
            origin_nview = self.style.display2normalisedViewport(
                (
                    origin_display[0] - x_min_offset,
                    origin_display[1] - y_min_offset
                )
            )

            # Calculate the far right border
            top_right_disp = self.style.world2display(self.style.GetImageWorldExtent())
            top_right_nview = self.style.display2normalisedViewport(
                (top_right_disp[0] + border + height, top_right_disp[1])
            )

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


