import vtk

class SliceSliderRepresentation(vtk.vtkSliderRepresentation2D):
    """A slider representation for the slice selector on a 2D CILViewer

    Parameters:
    -----------
    orientation: str, optional
        The orientation of the slider. Can be 'horizontal' or 'vertical'
    offset: float, optional
        The offset of the slider from the edge of the window. Default is 0.12

    """

    def __init__(self, orientation='horizontal', offset=0.12):
        self.tube_width = 0.004
        self.slider_length = 0.025
        self.slider_width = 0.015
        self.end_cap_length = 0.008
        self.end_cap_width = 0.02
        self.title_height = 0.02
        self.label_height = 0.02

        # self.value_minimum = 0.0
        # self.value_maximum = 1.0
        # self.value_initial = 1.0

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



        if orientation == 'vertical':
            self.offset = offset
            self.p1 = [self.end_cap_width * 1.1, self.offset]
            self.p2 = [self.end_cap_width * 1.1, 1 - self.offset]

        # super().__init__()
        # self.SetMinimumValue(self.value_minimum)
        # self.SetMaximumValue(self.value_maximum)
        # self.SetValue(self.value_initial)
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

        colors = vtk.vtkNamedColors()
        # Set the colors of the slider components.
        # Change the color of the bar.
        self.GetTubeProperty().SetColor(colors.GetColor3d(self.bar_color))
        # Change the color of the ends of the bar.
        self.GetCapProperty().SetColor(colors.GetColor3d(self.bar_ends_color))
        # Change the color of the knob that slides.
        self.GetSliderProperty().SetColor(colors.GetColor3d(self.slider_color))
        # Change the color of the knob when the mouse is held on it.
        self.GetSelectedProperty().SetColor(colors.GetColor3d(self.selected_color))
        # Change the color of the text displaying the value.
        # slider.GetLabelProperty().SetColor(colors.GetColor3d(self.value_color))
        # slider.GetLabelProperty().SetBackgroundColor(colors.GetColor3d(self.value_background_color))
        # slider.GetLabelProperty().ShadowOff()
        
        # slider.GetTitleProperty().SetColor(1,1,1)
        # slider.GetTitleProperty().ShadowOff()
        
        # next 2 lines go in CILViewer2D
        # slider_widget = vtk.vtkSliderWidget()
        # slider_widget.SetRepresentation(slider)

        # return slider_widget
    
    # def get_slider_text_label(self, position, text):
    #     colors = vtk.vtkNamedColors()
    #     # Create the TextActor
    #     text_actor = vtk.vtkTextActor()
    #     text_actor.SetInput(f"{text}")
    #     text_actor.GetTextProperty().SetColor(colors.GetColor3d('Lime'))

    #     # Create the text representation. Used for positioning the text_actor
    #     text_representation = vtk.vtkTextRepresentation()
    #     if position == 'min':
    #         p0 = [self.p1[0], self.p1[1] + 0.05]
    #     else:
    #         p0 = [self.p2[0], self.p2[1] + 0.05]
    #     text_representation.GetPositionCoordinate().SetValue(0.15, 0.15)
    #     text_representation.GetPosition2Coordinate().SetValue(0.7, 0.2)
    #     # text_representation.GetPositionCoordinate().SetValue(*p0)
    #     # text_representation.GetPosition2Coordinate().SetValue(*[el + 0.1 for el in p0])

    #     # Create the TextWidget
    #     # Note that the SelectableOff method MUST be invoked!
        
    #     text_widget = vtk.vtkTextWidget()
    #     text_widget.SetRepresentation(text_representation)

    #     text_widget.SetTextActor(text_actor)
    #     text_widget.SelectableOff()

    #     return text_widget, text_actor

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
        # self.viewer.sliderMinMaxLabels[1][1].SetInput("{}".format(maxslice))
        # self.viewer.sliderMinMaxLabels[1][1].SetInput("{}".format(0))
        self.update_from_viewer(caller, ev)
