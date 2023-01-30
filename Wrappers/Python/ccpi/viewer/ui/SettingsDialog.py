from eqt.ui import FormDialog, UISliderWidget
from PySide2 import QtWidgets, QtCore
from vtkmodules.util import colors

try:
    import matplotlib.pyplot as plt
except ImportError:
    # Add optional overload to allow plt.colormaps to be called without matplotlib
    from ccpi.viewer.utils import CILColorMaps

    class BackupColorMaps:
        @staticmethod
        def colormaps():
            return ["viridis", "plasma", "inferno", "magma"]

    plt = BackupColorMaps()


def background_color_list():
    initial_list = dir(colors)
    color_list = [
        {
            "text": "Miles blue",
            "value": "cil_viewer_blue",
        }
    ]

    initial_list.insert(0, initial_list.pop(initial_list.index("white")))
    initial_list.insert(1, initial_list.pop(initial_list.index("black")))

    for color in initial_list:
        if "__" in color:
            continue
        if "_" in color:
            filtered_color = color.replace("_", " ")
        else:
            filtered_color = color
        filtered_color = filtered_color.capitalize()
        color_list.append({"text": filtered_color, "value": color})

    return color_list


class DialogSettings(FormDialog):
    """Slice settings dialog."""

    def __init__(self, parent=None, title=None):
        FormDialog.__init__(self, parent, title=title)

        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)

        # Background color
        background_color = QtWidgets.QComboBox(self.groupBox)
        for i in background_color_list():
            background_color.addItem(i["text"])
        self.addWidget(background_color, "Background color", "background_color")

        # Slice orientation
        orientation = QtWidgets.QComboBox(self.groupBox)
        orientation.addItems(["YZ", "XZ", "XY"])
        orientation.setCurrentIndex(2)
        self.addWidget(orientation, "Orientation", "orientation")

        # Slice visibility
        slice_visibility = QtWidgets.QCheckBox("Slice Visibility", self.groupBox)
        self.addWidget(slice_visibility, "", "slice_visibility")

        # Auto window/level
        auto_window_level = QtWidgets.QPushButton("Auto Window/Level")
        self.addWidget(auto_window_level, "", "auto_window_level")

        # Slice window sliders
        slice_window_label = QtWidgets.QLabel("Slice Window")
        slice_window_slider = UISliderWidget.UISliderWidget(slice_window_label)
        self.addWidget(slice_window_slider, "Slice Window", "slice_window_slider")
        self.addWidget(slice_window_label, "", "slice_window_label")

        # Slice level sliders
        slice_level_label = QtWidgets.QLabel("Slice Level")
        slice_level_slider = UISliderWidget.UISliderWidget(slice_level_label)
        print(dir(slice_level_slider))
        self.addWidget(slice_level_slider, "Slice Level", "slice_level_slider")
        self.addWidget(slice_level_label, "", "slice_level_label")

        # Render save location
        render_save_location = QtWidgets.QLabel("Render save location")
        open_location_browser = QtWidgets.QPushButton("Open location browser")
        self.addWidget(render_save_location, "", "render_save_location")
        self.addWidget(open_location_browser, "", "open_location_browser")

    def get_settings(self):
        settings = {}
        for key, value in self.formWidget.widgets.items():
            if isinstance(value, QtWidgets.QLabel):
                settings[key] = value.text()
            elif isinstance(value, QtWidgets.QCheckBox):
                settings[key] = value.isChecked()
            elif isinstance(value, QtWidgets.QComboBox):
                settings[key] = value.currentIndex()
            elif isinstance(value, UISliderWidget.UISliderWidget):
                settings[key] = value.value()

        return settings

    def apply_settings(self, settings):
        for key, value in settings.items():
            widg = self.formWidget.widgets[key]
            if isinstance(widg, QtWidgets.QLabel):
                widg.setText(value)
            elif isinstance(widg, QtWidgets.QCheckBox):
                widg.setChecked(value)
            elif isinstance(widg, QtWidgets.QComboBox):
                widg.setCurrentIndex(value)
            elif isinstance(widg, UISliderWidget.UISliderWidget):
                widg.setValue(value)

    def auto_window_level(self):
        self.viewer.autoWindowLevelOnSliceRange()

        window_default = self.viewer.getSliceColorWindow()
        self.getWidget("slice_window_slider").setValue(window_default)

        level_default = self.viewer.getSliceColorLevel()
        self.getWidget("slice_level_slider").setValue(level_default)

    def set_viewer(self, viewer):
        """Attach the events to the viewer."""
        self.viewer = viewer

        # Orientation
        self.getWidget("orientation").currentIndexChanged.connect(self.change_viewer_orientation)

        # Slice visibility
        self.getWidget("slice_visibility").stateChanged.connect(self.viewer.style.ToggleSliceVisibility)

        # Auto window/level
        self.getWidget("auto_window_level").clicked.connect(self.auto_window_level)

        # Slice window sliders
        window_min, window_max = self.viewer.getImageMapRange((0.0, 100.0), "scalar")
        self.getWidget("slice_window_slider").setRange(window_min, window_max)
        self.getWidget("slice_window_slider").setTickInterval((window_max - window_min) / 10)
        window_default = self.viewer.getSliceColorWindow()
        self.getWidget("slice_window_slider").setValue(window_default)
        self.getWidget("slice_window_slider").valueChanged.connect(
            lambda: self.viewer.setSliceColorWindow(self.getWidget("slice_window_slider").value())
        )

        # Level window sliders
        level_min, level_max = self.viewer.getImageMapRange((0.0, 100.0), "scalar")
        self.getWidget("slice_level_slider").setRange(level_min, level_max)
        self.getWidget("slice_level_slider").setTickInterval((level_max - level_min) / 10)
        level_default = self.viewer.getSliceColorLevel()
        self.getWidget("slice_level_slider").setValue(level_default)
        self.getWidget("slice_level_slider").valueChanged.connect(
            lambda: self.viewer.setSliceColorLevel(self.getWidget("slice_level_slider").value())
        )

        self.getWidget("open_location_browser").clicked.connect(self.open_file_location_dialog)

    def open_file_location_dialog(self):
        """Open file location dialog."""
        dialog = QtWidgets.QFileDialog()
        file_location = dialog.getSaveFileName(self, "Select File")[0]
        print(file_location)
        # folder_location = dialog.getExistingDirectory(self, "Select Directory")
        self.getWidget("render_save_location").setText(file_location)

    def change_viewer_orientation(self):
        index = self.getWidget("orientation").currentIndex()
        self.viewer.style.SetSliceOrientation(index)
        self.viewer.style.UpdatePipeline(resetcamera=True)

    def change_background_color(self):
        color = self.getWidget("background_color").currentText().replace(" ", "_").lower()
        if color == "miles_blue":
            color_data = (0.1, 0.2, 0.4)
        else:
            color_data = getattr(colors, color.lower())
        self.viewer.ren.SetBackground(color_data)
        self.viewer.updatePipeline()

    def adjust_slider(self, value):
        pass


class DialogVolumeRenderSettings(FormDialog):
    """Volume render settings dialogue."""

    def __init__(self, parent=None, title=None):
        FormDialog.__init__(self, parent, title=title)

        # Background color
        background_color = QtWidgets.QComboBox(self.groupBox)
        for i in background_color_list():
            background_color.addItem(i["text"])
        self.addWidget(background_color, "Background color", "background_color")

        # 3D Volume visibility
        volume_visibility = QtWidgets.QCheckBox("3D Volume Visibility", self.groupBox)
        self.addWidget(volume_visibility, "", "volume_visibility")

        # Windowing min
        windowing_label_min = QtWidgets.QLabel("Windowing min")
        windowing_slider_min = UISliderWidget.UISliderWidget(windowing_label_min)
        self.addWidget(windowing_slider_min, "Windowing min", "windowing_slider_min")
        self.addWidget(windowing_label_min, "", "windowing_label")

        # Windowing max
        windowing_label_max = QtWidgets.QLabel("Windowing max")
        windowing_slider_max = UISliderWidget.UISliderWidget(windowing_label_max)
        self.addWidget(windowing_slider_max, "Windowing max", "windowing_slider_max")
        self.addWidget(windowing_label_max, "", "windowing_label_max")

        # Opacity mapping
        opacity_mapping = QtWidgets.QComboBox(self.groupBox)
        opacity_mapping.addItems(["Scalar", "Gradient"])
        self.addWidget(opacity_mapping, "Opacity mapping", "opacity_mapping")

        # Color scheme
        color_scheme = QtWidgets.QComboBox(self.groupBox)
        color_scheme.addItems(plt.colormaps())
        self.addWidget(color_scheme, "Color scheme", "color_scheme")

        # Volume clipping
        volume_clipping = QtWidgets.QCheckBox("Volume clipping", self.groupBox)
        self.addWidget(volume_clipping, "", "volume_clipping")
        volume_clipping_reset = QtWidgets.QPushButton("Reset volume clipping", self.groupBox)
        self.addWidget(volume_clipping_reset, "", "volume_clipping_reset")

        # Color range min
        color_range_label_min = QtWidgets.QLabel("Color range min")
        color_range_slider_min = UISliderWidget.UISliderWidget(color_range_label_min)
        self.addWidget(color_range_slider_min, "Color range min", "color_range_slider_min")
        self.addWidget(color_range_label_min, "", "color_range_label_min")

        # Color range max
        color_range_label_max = QtWidgets.QLabel("Color range max")
        color_range_slider_max = UISliderWidget.UISliderWidget(color_range_label_max)
        self.addWidget(color_range_slider_max, "Color range max", "color_range_slider_max")
        self.addWidget(color_range_label_max, "", "color_range_label_max")

        # Disable 3D related widgets if volume visibility is not checked
        volume_visibility_checked = self.getWidget("volume_visibility").isChecked()
        self.getWidget("opacity_mapping").setEnabled(volume_visibility_checked)
        self.getWidget("color_scheme").setEnabled(volume_visibility_checked)
        self.getWidget("volume_clipping").setEnabled(volume_visibility_checked)
        self.getWidget("volume_clipping_reset").setEnabled(volume_visibility_checked)
        self.getWidget("color_range_slider_min").setEnabled(volume_visibility_checked)
        self.getWidget("color_range_slider_max").setEnabled(volume_visibility_checked)
        self.getWidget("windowing_slider_min").setEnabled(volume_visibility_checked)
        self.getWidget("windowing_slider_max").setEnabled(volume_visibility_checked)

    def change_background_color(self):
        color = self.getWidget("background_color").currentText().replace(" ", "_").lower()
        if color == "miles_blue":
            color_data = (0.1, 0.2, 0.4)
        else:
            color_data = getattr(colors, color.lower())
        self.viewer.ren.SetBackground(color_data)
        self.viewer.updatePipeline()

    def set_viewer(self, viewer):
        """Attach the events to the viewer."""
        self.viewer = viewer

        # Volume visibility
        self.getWidget("volume_visibility").stateChanged.connect(self.toggle_volume_visibility)

        # Opacity mapping
        self.getWidget("opacity_mapping").currentIndexChanged.connect(self.change_opacity_mapping)

        # Color scheme
        self.getWidget("color_scheme").currentIndexChanged.connect(self.change_color_scheme)

        # Volume clipping
        self.getWidget("volume_clipping").stateChanged.connect(self.viewer.style.ToggleVolumeClipping)

        # Reset volume clipping
        self.getWidget("volume_clipping_reset").clicked.connect(self.reset_volume_clipping)

        # Background color
        self.getWidget("background_color").currentIndexChanged.connect(self.change_background_color)

        # Color range slider min
        self.getWidget("color_range_slider_min").setRange(0, 100)
        self.getWidget("color_range_slider_min").setTickInterval(10)
        self.getWidget("color_range_slider_min").setValue(85)
        # self.getWidget("color_range_slider_min").valueChanged.connect(
        #     lambda: self.viewer.setVolumeColorPercentiles(
        #         self.getWidget("color_range_slider_min").value(), self.getWidget("color_range_slider_max").value()
        #     )
        # )
        self.getWidget("color_range_slider_min").valueChanged.connect(self.change_color_range_min)

        # Color range slider max
        self.getWidget("color_range_slider_max").setRange(0, 100)
        self.getWidget("color_range_slider_max").setTickInterval(10)
        self.getWidget("color_range_slider_max").setValue(95)
        # self.getWidget("color_range_slider_min").valueChanged.connect(
        #     lambda: self.viewer.setVolumeColorPercentiles(
        #         self.getWidget("color_range_slider_min").value(), self.getWidget("color_range_slider_max").value()
        #     )
        # )
        self.getWidget("color_range_slider_min").valueChanged.connect(self.change_color_range_max)

        # Windowing slider min
        self.getWidget("windowing_slider_min").setRange(0, 100)
        self.getWidget("windowing_slider_min").setTickInterval(10)
        self.getWidget("windowing_slider_min").setValue(80)
        self.getWidget("windowing_slider_min").valueChanged.connect(self.change_volume_opacity_min)

        # Windowing slider max
        self.getWidget("windowing_slider_max").setRange(0, 100)
        self.getWidget("windowing_slider_max").setTickInterval(10)
        self.getWidget("windowing_slider_max").setValue(99)
        self.getWidget("windowing_slider_max").valueChanged.connect(self.change_volume_opacity_max)

    def change_color_range_min(self):
        if self.getWidget("color_range_slider_min").value() >= self.getWidget("color_range_slider_max").value():
            self.getWidget("color_range_slider_min").setValue(self.getWidget("color_range_slider_max").value() - 1)

        self.change_color_range()

    def change_color_range_max(self):
        if self.getWidget("color_range_slider_max").value() <= self.getWidget("color_range_slider_min").value():
            self.getWidget("color_range_slider_max").setValue(self.getWidget("color_range_slider_min").value() + 1)
        self.change_color_range()

    def change_color_range(self):
        self.viewer.setVolumeColorPercentiles(
            self.getWidget("color_range_slider_min").value(), self.getWidget("color_range_slider_max").value()
        )

    def change_volume_opacity_min(self):
        if self.getWidget("windowing_slider_min").value() >= self.getWidget("windowing_slider_max").value():
            self.getWidget("windowing_slider_min").setValue(self.getWidget("windowing_slider_max").value() - 1)

        self.change_volume_opacity()

    def change_volume_opacity_max(self):
        if self.getWidget("windowing_slider_max").value() <= self.getWidget("windowing_slider_min").value():
            self.getWidget("windowing_slider_max").setValue(self.getWidget("windowing_slider_min").value() + 1)

        self.change_volume_opacity()

    def change_volume_opacity(self):
        opacity = self.getWidget("opacity_mapping").currentText()
        if opacity == "Gradient":
            opacity_min, opacity_max = (
                self.getWidget("windowing_slider_min").value(),
                self.getWidget("windowing_slider_max").value(),
            )
            self.viewer.setGradientOpacityPercentiles(opacity_min, opacity_max)
        elif opacity == "Scalar":
            opacity_min, opacity_max = (
                self.getWidget("windowing_slider_min").value(),
                self.getWidget("windowing_slider_max").value(),
            )
            self.viewer.setScalarOpacityPercentiles(opacity_min, opacity_max)

    def reset_volume_clipping(self):
        self.getWidget("volume_clipping").setChecked(False)
        if self.viewer.volume_render_initialised:
            if self.viewer.volume.GetMapper().GetClippingPlanes() is not None:
                self.viewer.volume.GetMapper().RemoveAllClippingPlanes()
        if self.viewer.clipping_plane_initialised:
            self.viewer.style.SetVolumeClipping(False)
            self.remove_clipping_plane()

    def remove_clipping_plane(self):
        if hasattr(self.viewer, "planew"):
            self.viewer.remove_clipping_plane()
            self.viewer.getRenderer().Render()
            self.viewer.updatePipeline()

    def get_settings(self):
        settings = {}
        for key, value in self.formWidget.widgets.items():
            if isinstance(value, QtWidgets.QLabel):
                settings[key] = value.text()
            elif isinstance(value, QtWidgets.QCheckBox):
                settings[key] = value.isChecked()
            elif isinstance(value, QtWidgets.QComboBox):
                settings[key] = value.currentIndex()

        return settings

    def apply_settings(self, settings):
        for key, value in settings.items():
            widg = self.formWidget.widgets[key]
            if isinstance(widg, QtWidgets.QLabel):
                widg.setText(value)
            elif isinstance(widg, QtWidgets.QCheckBox):
                widg.setChecked(value)
            elif isinstance(widg, QtWidgets.QComboBox):
                widg.setCurrentIndex(value)

    def toggle_volume_visibility(self):
        # Set 3D widgets enabled/disabled depending on volume visibility checkbox
        volume_visibility_checked = self.getWidget("volume_visibility").isChecked()
        self.getWidget("windowing_slider_min").setEnabled(volume_visibility_checked)
        self.getWidget("windowing_slider_max").setEnabled(volume_visibility_checked)
        self.getWidget("opacity_mapping").setEnabled(volume_visibility_checked)
        self.getWidget("color_scheme").setEnabled(volume_visibility_checked)
        self.getWidget("volume_clipping").setEnabled(volume_visibility_checked)
        self.getWidget("volume_clipping_reset").setEnabled(volume_visibility_checked)
        self.getWidget("color_range_slider_min").setEnabled(volume_visibility_checked)
        self.getWidget("color_range_slider_max").setEnabled(volume_visibility_checked)

        self.viewer.style.ToggleVolumeVisibility()

        if volume_visibility_checked:
            self.change_opacity_mapping()

        self.viewer.updateVolumePipeline()

    def change_opacity_mapping(self):
        method = self.getWidget("opacity_mapping").currentText().lower()
        self.viewer.setVolumeRenderOpacityMethod(method)
        self.viewer.updateVolumePipeline()

    def change_color_scheme(self):
        color_scheme = self.getWidget("color_scheme").currentText()
        self.viewer.setVolumeColorMapName(color_scheme)
        self.viewer.updateVolumePipeline()
