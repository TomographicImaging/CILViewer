import vtk
import logging

logger = logging.getLogger(__name__)


class SliceSliderRepresentation(vtk.vtkSliderRepresentation2D):
    """A slider representation for the slice selector slider on a 2D CILViewer

    Parameters
    -----------
    orientation: str, optional
        The orientation of the slider. Can be 'horizontal' or 'vertical'
    offset: float, optional
        The offset of the slider from the edge of the window. Default is 0.12

    """

    def __init__(self, orientation='horizontal', offset=0.12):
        self.tube_width = 0.004
        self.slider_length = 0.015
        self.slider_width = 0.015
        self.end_cap_length = 0.008
        self.end_cap_width = 0.02
        self.title_height = 0.02
        self.label_height = 0.02
        self.bar_color = 'Gray'
        cil_pink = [[el / 0xff for el in [0xe5, 0x06, 0x95]], [el / 0xff for el in [0xc9, 0x2c, 0x99]],
                    [el / 0xff for el in [0x99, 0x3d, 0xbb]], [el / 0xff for el in [0x51, 0x0c, 0x76]]]

        self.orientation = 'horizontal'
        self.offset = 0.12

        self.p1 = [self.offset, self.end_cap_width * 1.1]
        self.p2 = [1 - self.offset, self.end_cap_width * 1.1]

        self.title = None

        if orientation == 'vertical':
            self.offset = offset
            self.p1 = [self.end_cap_width * 1.1, self.offset]
            self.p2 = [self.end_cap_width * 1.1, 1 - self.offset]

        self.SetTitleText(self.title)

        self.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
        self.GetPoint1Coordinate().SetValue(self.p1[0], self.p1[1])
        self.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
        self.GetPoint2Coordinate().SetValue(self.p2[0], self.p2[1])

        self.SetTubeWidth(self.tube_width)
        self.SetSliderLength(self.slider_length)
        # slider_width = self.tube_width
        # slider.SetSliderWidth(slider_width)
        self.SetEndCapLength(self.end_cap_length)
        self.SetEndCapWidth(self.end_cap_width)
        self.SetTitleHeight(self.title_height)
        self.SetLabelHeight(self.label_height)

        # Set the colors of the slider components.
        # Change the color of the bar.
        self.GetTubeProperty().SetColor(vtk.vtkNamedColors().GetColor3d(self.bar_color))
        # Change the color of the ends of the bar.
        self.GetCapProperty().SetColor(cil_pink[2])
        # Change the color of the knob that slides.
        self.GetSliderProperty().SetColor(cil_pink[1])
        # Change the color of the knob when the mouse is held on it.
        self.GetSelectedProperty().SetColor(cil_pink[0])


class SliderCallback:
    '''
    Class to propagate the effects of interaction between the slider widget and the viewer 
    the slider is embedded into, and viceversa.
    
    Parameters
    -----------
    viewer : CILViewer2D the slider is embedded into
    slider_widget : the vtkSliderWidget that is embedded in the viewer
    '''

    def __init__(self, viewer, slider_widget):
        self.viewer = viewer
        self.slider_widget = slider_widget

    def __call__(self, caller, ev):
        '''Update the slice displayed by the viewer when the slider is moved
        
        Parameters
        -----------
        caller : the slider widget
        ev : the event that triggered the update
        '''
        slider_widget = caller
        value = slider_widget.GetRepresentation().GetValue()
        self.viewer.displaySlice(int(value))
        self.update_label(value)

    def update_label(self, value):
        '''Update the text label on the slider. This is called by update_from_viewer
        
        Parameters
        -----------
        value : the value to be displayed on text label the slider
        '''
        rep = self.slider_widget.GetRepresentation()
        maxval = rep.GetMaximumValue()
        txt = "{}/{}".format(int(value), int(maxval))
        rep.SetLabelFormat(txt)

    def update_from_viewer(self, caller, ev):
        '''Update the slider widget from the viewer. This is called when the viewer changes the slice
        
        Parameters
        -----------
        caller : the interactor style
        ev : the event that triggered the update
        '''
        # The caller is the interactor style
        logger.info(f"Updating for event {ev}")
        value = caller.GetActiveSlice()
        self.slider_widget.GetRepresentation().SetValue(value)
        self.update_label(value)
        caller.GetRenderWindow().Render()

    def update_orientation(self, caller, ev):
        '''Update the slider widget when the orientation is changed

        Parameters
        -----------
        caller : the interactor style
        ev : the event that triggered the update
        '''
        logger.info(f"Updating orientation {ev}")
        value = caller.GetActiveSlice()
        dims = caller._viewer.img3D.GetDimensions()
        maxslice = dims[caller.GetSliceOrientation()] - 1
        self.slider_widget.GetRepresentation().SetMaximumValue(maxslice)
        self.update_from_viewer(caller, ev)
