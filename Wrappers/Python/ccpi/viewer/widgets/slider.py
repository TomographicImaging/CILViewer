import vtk

class SliderProperties:
    def __init__(self):
        self.tube_width = 0.004
        self.slider_length = 0.025
        self.slider_width = 0.015
        self.end_cap_length = 0.008
        self.end_cap_width = 0.02
        self.title_height = 0.02
        self.label_height = 0.02

        self.value_minimum = 0.0
        self.value_maximum = 1.0
        self.value_initial = 1.0

        self.orientation = 'horizontal'
        self.offset = 0.12

        self.p1 = [self.offset, self.end_cap_width * 1.1]
        self.p2 = [1 - self.offset, self.end_cap_width * 1.1]

        self.title = None

        self.title_color = 'Black'
        self.label_color = 'White'
        self.value_color = 'White'
        self.value_background_color = 'Black'
        self.slider_color = 'Lime'
        self.selected_color = 'Lime'
        self.bar_color = 'Gray'
        self.bar_ends_color = 'Yellow'


    def make_slider_widget(self, orientation='horizontal', offset=0.12):
        """
        Make the slider widget based on the properties of this class.

        
        Returns
        -------
        A configured vtkSliderWidget with its vtkSliderRepresentation2D.

        """

        if orientation == 'vertical':
            self.offset = offset
            self.p1 = [self.end_cap_width * 1.1, self.offset]
            self.p2 = [self.end_cap_width * 1.1, 1 - self.offset]

        slider = vtk.vtkSliderRepresentation2D()

        slider.SetMinimumValue(self.value_minimum)
        slider.SetMaximumValue(self.value_maximum)
        slider.SetValue(self.value_initial)
        slider.SetTitleText(self.title)

        slider.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
        slider.GetPoint1Coordinate().SetValue(self.p1[0], self.p1[1])
        slider.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
        slider.GetPoint2Coordinate().SetValue(self.p2[0], self.p2[1])

        slider.SetTubeWidth(self.tube_width)
        slider.SetSliderLength(self.slider_length)
        slider.SetSliderWidth(self.slider_width)
        slider.SetEndCapLength(self.end_cap_length)
        slider.SetEndCapWidth(self.end_cap_width)
        slider.SetTitleHeight(self.title_height)
        slider.SetLabelHeight(self.label_height)

        colors = vtk.vtkNamedColors()
        # Set the colors of the slider components.
        # Change the color of the bar.
        slider.GetTubeProperty().SetColor(colors.GetColor3d(self.bar_color))
        # Change the color of the ends of the bar.
        slider.GetCapProperty().SetColor(colors.GetColor3d(self.bar_ends_color))
        # Change the color of the knob that slides.
        slider.GetSliderProperty().SetColor(colors.GetColor3d(self.slider_color))
        # Change the color of the knob when the mouse is held on it.
        slider.GetSelectedProperty().SetColor(colors.GetColor3d(self.selected_color))
        # Change the color of the text displaying the value.
        slider.GetLabelProperty().SetColor(colors.GetColor3d(self.value_color))
        slider.GetLabelProperty().SetBackgroundColor(colors.GetColor3d(self.value_background_color))
        slider.GetLabelProperty().ShadowOff()
        
        slider.GetTitleProperty().SetColor(1,1,1)
        slider.GetTitleProperty().ShadowOff()
        
        slider_widget = vtk.vtkSliderWidget()
        slider_widget.SetRepresentation(slider)

        return slider_widget

class SliderCallback:
    '''
    Class to propagate the effects of interaction between the slider widget and the viewer 
    the slider is embedded into.
    
    Parameters:
    -----------

    - viewer, CILViewer2D the slider is embedded into
    - slider_widget, the vtkSliderWidget that is embedded in the viewer
    '''
    def __init__(self, viewer, slider_widget):
        self.viewer = viewer
        self.slider_widget = slider_widget

    def __call__(self, caller, ev):
        slider_widget = caller
        value = slider_widget.GetRepresentation().GetValue()
        self.viewer.displaySlice(int(value))
        self.update_label(slider_widget, value)
    
    def update_label(self, slider_widget, value):
        rep = slider_widget.GetRepresentation()
        maxval = rep.GetMaximumValue()
        txt = "Slice {}/{}".format(int(value), int(maxval))
        rep.SetLabelFormat(txt)

    def update_from_viewer(self, caller, ev):
        # The caller is the interactor style
        value = caller.GetActiveSlice()
        self.slider_widget.GetRepresentation().SetValue(value)
        self.update_label(self.slider_widget, value)
        caller.GetRenderWindow().Render()

    def update_orientation(self, caller, ev):
        value = caller.GetActiveSlice()
        dims = caller._viewer.img3D.GetDimensions()
        maxslice = dims[caller.GetSliceOrientation()] -1
        self.slider_widget.GetRepresentation().SetMaximumValue(maxslice)
        self.update_from_viewer(caller, ev)
