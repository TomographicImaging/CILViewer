
import vtk
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

class CILViewerBase():

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

        # holder for list of actors
        self.actors = {}

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

    def getInteractor(self):
        return self.iren

    def getRenderer(self):
        return self.ren
    
    def getRenderWindow(self):
        '''returns the render window'''
        return self.renWin

    def getSliceOrientation(self):
        return self.sliceOrientation

    def setActiveSlice(self, sliceno):
        self.slicenos[self.getSliceOrientation()] = sliceno

    def getActiveSlice(self):
        return self.slicenos[self.getSliceOrientation()]

    def getSliceColorWindow(self):
        return self.imageSlice.GetProperty().GetColorWindow()

    def getSliceColorLevel(self):
        return self.imageSlice.GetProperty().GetColorLevel()

    def getSliceWindowLevelFromRange(self, cmin, cmax):
        # set the level to the average between the percentiles
        level = (cmin + cmax) / 2
        # accommodates all values between the level an the percentiles
        window = cmax - cmin

        return window, level

    def startRenderLoop(self):
        self.iren.Start()

    def getImageHistogramStatistics(self, method):
        '''
        returns histogram statistics for either the image
        or gradient of the image depending on the method
        '''
        ia = vtk.vtkImageHistogramStatistics()
        if method == 'scalar':
            ia.SetInputData(self.img3D)
        else:
            grad = vtk.vtkImageGradientMagnitude()
            grad.SetInputData(self.img3D)
            grad.SetDimensionality(3)
            grad.Update()
            ia.SetInputData(grad.GetOutput())
        ia.Update()
        return ia

    def getVolumeMapRange(self, percentiles, method):
        '''
        uses percentiles to generate min and max values in either
        the image or image gradient (depending on method) for which
        the colormap or opacity are displayed.
        '''
        ia = self.getImageHistogramStatistics(method)
        ia.SetAutoRangePercentiles(*percentiles)
        ia.Update()
        min, max = ia.GetAutoRange()
        return min, max

    def getVolumeRange(self, method):
        '''
        Parameters
        -----------
        method: string : ['scalar', 'gradient']
            'scalar' - returns full range of values in image
            'gradient' - returns full range of values in image gradient
        '''

        return self.getVolumeMapRange((0, 100), method)

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
        # Level is the average of min and max, and the window is the difference.
        self.imageSlice.GetProperty().SetColorLevel(level)
        self.imageSlice.GetProperty().SetColorWindow(window)
        self.imageSlice.Update()
        self.ren.Render()
        self.renWin.Render()

    def setSliceColorPercentiles(self, min_percentage, max_percentage):
        #TODO: LATER: FIX THIS METHOD - IT DOESN'T WORK CORRECTLY
        min_val, max_val = self.getVolumeMapRange((min_percentage, max_percentage), 'scalar')
        self.setSliceColorWindowLevel(min_val, max_val)

    def setSliceColorWindow(self, window):
        self.imageSlice.GetProperty().SetColorWindow(window)
        self.imageSlice.Update()
        self.ren.Render()
        self.renWin.Render()

    def setSliceColorLevel(self, level):
        self.imageSlice.GetProperty().SetColorLevel(level)
        self.imageSlice.Update()
        self.ren.Render()
        self.renWin.Render()

    def getSliceMapRange(self, percentiles):
        ia = vtk.vtkImageHistogramStatistics()
        ia.SetInputData(self.img3D)
        ia.SetAutoRangePercentiles(*percentiles)
        ia.Update()
        min, max = ia.GetAutoRange()
        return min, max

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