import vtk
from ccpi.viewer import (ALT_KEY, CONTROL_KEY, CROSSHAIR_ACTOR, CURSOR_ACTOR, HELP_ACTOR, HISTOGRAM_ACTOR,
                         LINEPLOT_ACTOR, OVERLAY_ACTOR, SHIFT_KEY, SLICE_ACTOR, SLICE_ORIENTATION_XY,
                         SLICE_ORIENTATION_XZ, SLICE_ORIENTATION_YZ)
from ccpi.viewer.utils.io import SaveRenderToPNG
import logging


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


class CILViewerBase():
    '''
    Base Class for CILViewers.

    When making a subclass, the following must be set in the __init__:

    self.setInteractorStyle(style)

    '''

    def __init__(self, dimx=600, dimy=600, renWin=None, iren=None, ren=None, debug=False):
        # Handle arguments:
        # create a renderer
        if ren is None:
            ren = vtk.vtkRenderer()
        self.ren = ren

        # create a rendering window
        if renWin is None:
            renWin = vtk.vtkRenderWindow()

        renWin.SetSize(dimx, dimy)
        renWin.AddRenderer(self.ren)
        self.renWin = renWin

        if iren is not None:
            self.iren = iren
        else:
            self.iren = vtk.vtkRenderWindowInteractor()

        self.iren.SetRenderWindow(self.renWin)

        self.ren.SetBackground(.1, .2, .4)

        # img 3D as slice
        self.img3D = None
        self.slicenos = [0, 0, 0]
        self.sliceOrientation = SLICE_ORIENTATION_XY

        imageSlice = vtk.vtkImageSlice()
        imageSliceMapper = vtk.vtkImageSliceMapper()
        imageSlice.SetMapper(imageSliceMapper)
        imageSlice.GetProperty().SetInterpolationTypeToNearest()
        self.imageSlice = imageSlice
        self.imageSliceMapper = imageSliceMapper

        self.voi = vtk.vtkExtractVOI()
        self.ia = vtk.vtkImageHistogramStatistics()
        self.ia.SetAutoRangePercentiles(5.0, 95.)

        self.helpActor = vtk.vtkActor2D()
        self.helpActor.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
        self.helpActor.GetPositionCoordinate().SetValue(0.1, 0.5)
        self.helpActor.VisibilityOff()

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
        # axes labels
        self.axisLabelsText = self.getCurrentAxisLabelsText()

        # holder for list of actors and widgets
        self.actors = {}
        self.widgets = {}

        #initial Window/Level
        self.InitialLevel = 0
        self.InitialWindow = 0

        #ViewerEvent
        self.event = ViewerEventManager()

        self.histogramPlotActor = vtk.vtkXYPlotActor()
        self.histogramPlotActor.ExchangeAxesOff()
        self.histogramPlotActor.SetXLabelFormat("%g")
        self.histogramPlotActor.SetXLabelFormat("%g")
        self.histogramPlotActor.SetAdjustXLabels(3)
        self.histogramPlotActor.SetXTitle("Level")
        self.histogramPlotActor.SetYTitle("N")
        self.histogramPlotActor.SetXValuesToValue()
        self.histogramPlotActor.SetPlotColor(0, (0, 1, 1))

    def setInteractorStyle(self, style):
        self.style = style
        self.iren.SetInteractorStyle(self.style)
        self.iren.Initialize()

    def getInteractor(self):
        return self.iren

    def getRenderer(self):
        return self.ren

    def getRenderWindow(self):
        '''returns the render window'''
        return self.renWin

    def getCamera(self):
        '''returns the active camera'''
        return self.ren.GetActiveCamera()

    def startRenderLoop(self):
        self.iren.Start()

    def saveRender(self, filename, renWin=None):
        '''Save the render window to PNG file'''
        if renWin is None:
            renWin = self.renWin
        SaveRenderToPNG(self.renWin, filename)

    def validateValue(self, value, axis):
        dims = self.img3D.GetDimensions()
        max_slice = [x - 1 for x in dims]

        axis_int = {'x': SLICE_ORIENTATION_YZ, 'y': SLICE_ORIENTATION_XZ, 'z': SLICE_ORIENTATION_XY}

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

    # METHODS ON THE FULL 3D IMAGE DATA: ------------------------------------------------

    def setInput3DData(self, imageData):
        raise NotImplementedError("Implemented in the subclasses.")

    def getImageHistogramStatistics(self, method, slice=False):
        '''
        returns histogram statistics for either the image
        or gradient of the image depending on the method
        if slice = True, calculates for the slice instead of
        the entire image volume.
        '''
        ia = vtk.vtkImageHistogramStatistics()

        if slice:
            input_data = self.voi.GetOutput()
        else:
            input_data = self.img3D

        if method == 'scalar':
            ia.SetInputData(input_data)
        else:
            grad = vtk.vtkImageGradientMagnitude()
            grad.SetInputData(input_data)
            grad.SetDimensionality(3)
            grad.Update()
            ia.SetInputData(grad.GetOutput())
        ia.Update()
        return ia

    def getImageMapRange(self, percentiles, method):
        '''
        uses percentiles to generate min and max values in either
        the image or image gradient (depending on method) for which
        the colormap or opacity are displayed.
        '''
        ia = self.getImageHistogramStatistics(method)
        ia.SetAutoRangePercentiles(*percentiles)
        ia.Update()
        min, max = ia.GetAutoRange()
        logging.debug(f"getImageMapRange: method{method}")
        logging.debug(f"getImageMapRange: percentiles {percentiles}")
        logging.debug(f"getImageMapRange: whole range ({ia.GetMinimum()}, {ia.GetMaximum()})")
        logging.debug(f"getImageMapRange: percentile range ({min}, {max})")
        return min, max

    def getImageMapWholeRange(self, method):
        '''
        Parameters
        -----------
        method: string : ['scalar', 'gradient']
            'scalar' - returns full range of values in the 3D image
            'gradient' - returns full range of values in 3D image's gradient
        '''

        ia = self.getImageHistogramStatistics(method)

        return ia.GetMinimum(), ia.GetMaximum()

    # METHODS ON THE SLICE: --------------------------------------------------------

    def getSliceOrientation(self):
        return self.sliceOrientation

    def setActiveSlice(self, sliceno):
        self.slicenos[self.getSliceOrientation()] = sliceno

    def getActiveSlice(self):
        return self.slicenos[self.getSliceOrientation()]

    # Set interpolation on
    def setInterpolateOn(self):
        self.imageSlice.GetProperty().SetInterpolationTypeToLinear()
        self.renWin.Render()

    # Set interpolation off
    def setInterpolateOff(self):
        self.imageSlice.GetProperty()\
            .SetInterpolationTypeToNearest()
        self.renWin.Render()

    def setSliceColorWindowLevel(self, window, level):
        '''
        Set the window and level for the 2D slice of the 3D image.
        '''
        # Level is the average of min and max, and the window is the difference.
        self.imageSlice.GetProperty().SetColorLevel(level)
        self.imageSlice.GetProperty().SetColorWindow(window)
        self.imageSlice.Update()
        self.ren.Render()
        self.renWin.Render()

    def setSliceColorPercentiles(self, min_percentage, max_percentage):
        min_val, max_val = self.getSliceMapRange((min_percentage, max_percentage), 'scalar')
        self.setSliceMapRange(min_val, max_val)

    def getSliceColorPercentiles(self):
        min_val, max_val = self.getSliceMapWholeRange('scalar')
        min_color, max_color = self.getSliceMapRange()
        min_percentage = (min_color - min_val) / (max_val - min_val) * 100
        max_percentage = (max_color - min_val) / (max_val - min_val) * 100
        return min_percentage, max_percentage

    def setSliceColorWindow(self, window):
        '''
        Set the window for the 2D slice of the 3D image.
        '''
        self.imageSlice.GetProperty().SetColorWindow(window)
        self.imageSlice.Update()
        self.ren.Render()
        self.renWin.Render()

    def setSliceColorLevel(self, level):
        '''
        Set the level for the 2D slice of the 3D image.
        '''
        self.imageSlice.GetProperty().SetColorLevel(level)
        self.imageSlice.Update()
        self.ren.Render()
        self.renWin.Render()

    def getSliceColorWindow(self):
        '''
        Get the window for the 2D slice of the 3D image.
        '''
        return self.imageSlice.GetProperty().GetColorWindow()

    def getSliceColorLevel(self):
        '''
        Get the level for the 2D slice of the 3D image.
        '''
        return self.imageSlice.GetProperty().GetColorLevel()

    def getSliceWindowLevelFromRange(self, cmin, cmax):
        # set the level to the average between the percentiles
        level = (cmin + cmax) / 2
        # accommodates all values between the level and the percentiles
        window = cmax - cmin

        return window, level

    def getSliceMapWholeRange(self, method):
        '''
        Parameters
        -----------
        method: string : ['scalar', 'gradient']
            'scalar' - returns full range of values in image slice
            'gradient' - returns full range of values in image slice's gradient
        '''

        return self.getSliceMapRange((0, 100), method)

    def getSliceMapRange(self, percentiles, method='scalar'):
        '''
        uses percentiles to generate min and max values in
        the 2D slice of the 3D image, for which
        the colormap is displayed.
        '''

        ia = self.getImageHistogramStatistics(method, slice=True)
        ia.SetAutoRangePercentiles(*percentiles)
        ia.Update()
        min, max = ia.GetAutoRange()
        return min, max

    def setSliceMapRange(self, min, max):
        '''
        Parameters
        -----------
        min, max: float, default: the raw value of the 80. percentile for min, and the raw value of the 99. percentile for max.
            the upper and lower image values that the 
            color will be mapped to.
        update_pipeline: bool
            whether to immediately update the pipeline with this new
            setting
        '''
        window, level = self.getSliceWindowLevelFromRange(min, max)
        self.setSliceColorLevel(level)
        self.setSliceColorWindow(window)

    def autoWindowLevelOnSliceRange(self, update_slice=True):
        '''Auto-adjusts window-level for the slice, based on the 5 and 95th percentiles of the current slice.'''
        self.ia.SetAutoRangePercentiles(5.0, 95.)
        cmin, cmax = self.ia.GetAutoRange()
        window, level = self.getSliceWindowLevelFromRange(cmin, cmax)

        self.imageSlice.GetProperty().SetColorLevel(level)
        self.imageSlice.GetProperty().SetColorWindow(window)

        if update_slice:
            self.style.UpdateImageSlice()

    def addWidgetReference(self, widget, name):
        '''Adds widget to dictionary of widgets'''
        if self.getWidget(name) is not None:
            raise ValueError(f'Could not save reference to widget, as a widget with name {name} already exists.')
        self.widgets[name] = widget

    def getWidget(self, name):
        return self.widgets.get(name)

    def deleteWidget(self, name):
        ''' deletes a widget
        Parameters:
        name: string
            reference name given to the widget in the 
            dictionary of widgets'''

        widget = self.getWidget(name)

        if widget is not None:
            widget.Off()
            del widget
            self.widgets.pop(name)

    def setVisualisationDownsampling(self, value):
        self.visualisation_downsampling = value
        if value != [1, 1, 1]:
            self.image_is_downsampled = True
        else:
            self.image_is_downsampled = False

    def getVisualisationDownsampling(self):
        return self.visualisation_downsampling

    def getCurrentAxisLabelsText(self):
        '''Returns the current labels on the axis widget.'''
        om = self.orientation_marker.GetOrientationMarker()
        return [om.GetXAxisLabelText(), om.GetYAxisLabelText(), om.GetZAxisLabelText()]

    def setAxisLabels(self, labels=['x', 'y', 'z'], overwrite_flag=True):
        '''Sets the axes widget labels.
        
        Parameters
        ----------
        labels : list of str
        overwrite_flag : bool
            If True the attribute 'axisLabelText' is overwritten, if False it is not overwritten'''
        if type(labels) != list:
            raise TypeError("Labels must be a list of strings")
        if overwrite_flag is True:
            self.axisLabelsText = labels
        om = self.orientation_marker.GetOrientationMarker()
        om.SetXAxisLabelText(labels[0])
        om.SetYAxisLabelText(labels[1])
        om.SetZAxisLabelText(labels[2])
