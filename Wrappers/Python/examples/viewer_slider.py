# inspired by https://examples.vtk.org/site/Python/Visualization/FroggieView/
import vtk
from ccpi.viewer import viewer2D


class SliderProperties:
    tube_width = 0.004
    slider_length = 0.015
    slider_width = 0.008
    end_cap_length = 0.008
    end_cap_width = 0.02
    title_height = 0.02
    label_height = 0.02

    value_minimum = 0.0
    value_maximum = 1.0
    value_initial = 1.0

    p1 = [0.12, end_cap_width * 1.1]
    p2 = [0.88, end_cap_width * 1.1]

    title = None

    title_color = 'Black'
    label_color = 'White'
    value_color = 'White'
    value_background_color = 'Black'
    slider_color = 'Lime'
    selected_color = 'Lime'
    bar_color = 'Gray'
    bar_ends_color = 'Yellow'


def make_slider_widget(properties):
    """
    Make the slider widget.

    :param properties: The slider properties.
    :param lut: The color lookup table.
    :param idx: The tissue index.
    :return: The slider widget.
    """
    slider = vtk.vtkSliderRepresentation2D()

    slider.SetMinimumValue(properties.value_minimum)
    slider.SetMaximumValue(properties.value_maximum)
    slider.SetValue(properties.value_initial)
    slider.SetTitleText(properties.title)

    slider.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
    slider.GetPoint1Coordinate().SetValue(properties.p1[0], properties.p1[1])
    slider.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
    slider.GetPoint2Coordinate().SetValue(properties.p2[0], properties.p2[1])

    slider.SetTubeWidth(properties.tube_width)
    slider.SetSliderLength(properties.slider_length)
    slider.SetSliderWidth(properties.slider_width)
    slider.SetEndCapLength(properties.end_cap_length)
    slider.SetEndCapWidth(properties.end_cap_width)
    slider.SetTitleHeight(properties.title_height)
    slider.SetLabelHeight(properties.label_height)

    colors = vtk.vtkNamedColors()
    # Set the colors of the slider components.
    # Change the color of the bar.
    slider.GetTubeProperty().SetColor(colors.GetColor3d(properties.bar_color))
    # Change the color of the ends of the bar.
    slider.GetCapProperty().SetColor(colors.GetColor3d(properties.bar_ends_color))
    # Change the color of the knob that slides.
    slider.GetSliderProperty().SetColor(colors.GetColor3d(properties.slider_color))
    # Change the color of the knob when the mouse is held on it.
    slider.GetSelectedProperty().SetColor(colors.GetColor3d(properties.selected_color))
    # Change the color of the text displaying the value.
    slider.GetLabelProperty().SetColor(colors.GetColor3d(properties.value_color))
    slider.GetLabelProperty().SetBackgroundColor(colors.GetColor3d(properties.value_background_color))
    slider.GetLabelProperty().ShadowOff()
    #  Use the one color for the labels.
    # slider.GetTitleProperty().SetColor(colors.GetColor3d(properties.label_color))
    # Change the color of the text indicating what the slider controls
    
    slider.GetTitleProperty().SetColor(1,1,1)
    slider.GetTitleProperty().ShadowOff()
    
    slider_widget = vtk.vtkSliderWidget()
    slider_widget.SetRepresentation(slider)

    return slider_widget


class SliderCallback:
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
        self.update_label(slider_widget, value)


if __name__ == '__main__':
    v = viewer2D()
    slider_properties = SliderProperties()
    slider_properties.title = ""


    from ccpi.viewer.utils.io import ImageReader
    import os
    reader = ImageReader(r"C:\Users\ofn77899\Data\dvc/frame_000_f.npy", resample=False)
    # reader = ImageReader(r"{}/head_uncompressed.mha".format(os.path.dirname(__file__)), resample=False)
    
    data = reader.Read()
    slider_properties.value_minimum = 0
    # slider_properties.value_maximum = reader.GetOutput().GetDimensions()[2] - 1
    slider_properties.value_maximum = data.GetDimensions()[2] - 1
    

    # v.setInputData(reader.GetOutput())
    v.setInputData(data)
    slider_properties.value_initial = v.getActiveSlice()
    slider_widget = make_slider_widget(slider_properties)

    slider_widget.SetInteractor(v.getInteractor())
    slider_widget.SetAnimationModeToAnimate()
    slider_widget.EnabledOn()

    cb = SliderCallback(v, slider_widget)
    slider_widget.AddObserver(vtk.vtkCommand.InteractionEvent, cb)

    v.style.AddObserver("MouseWheelForwardEvent", cb.update_from_viewer, 0.9 )
    v.style.AddObserver("MouseWheelBackwardEvent", cb.update_from_viewer, 0.9 )

    cb(slider_widget, None)
    v.startRenderLoop()
