from eqt.ui import FormDialog, UISliderWidget
from PySide2 import QtWidgets


class Dialogue2D(FormDialog):
    def __init__(self, parent=None, title=None):
        FormDialog.__init__(self, parent, title=title)

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
        self.addWidget(slice_level_slider, "Slice Level", "slice_level_slider")
        self.addWidget(slice_level_label, "", "slice_level_label")

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
        # Attach the events to the viewer
        # TODO: create separate function for sliders

        self.getWidget("orientation").currentIndexChanged.connect(self.change_viewer_orientation)
        self.viewer = viewer

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

    def adjust_slider(self, value):
        pass
        # self.viewer.setSliceColorWindow(value)
        # self.getWidget("slice_window_label").setText("Slice Window: " + str(value))

    def change_viewer_orientation(self):
        index = self.getWidget("orientation").currentIndex()
        self.viewer.style.SetSliceOrientation(index)
        self.viewer.style.UpdatePipeline(resetcamera=True)


# window and level sliders - level and range
# labels current value of slider label


class Dialogue3D(FormDialog):  # volume settings
    def __init__(self, parent=None, title=None):
        FormDialog.__init__(self, parent, title=title)

        # 3D Volume visibility
        volume_visibility = QtWidgets.QCheckBox("3D Volume Visibility", self.groupBox)
        self.addWidget(volume_visibility, "", "volume_visibility")

        # Opacity mapping
        opacity_mapping = QtWidgets.QComboBox(self.groupBox)
        opacity_mapping.addItems(["Scalar", "Gradient"])
        self.addWidget(opacity_mapping, "Opacity mapping", "opacity_mapping")

        # Color scheme
        color_scheme = QtWidgets.QComboBox(self.groupBox)
        color_scheme.addItems(["Grey", "Rainbow", "Hot Metal"])
        self.addWidget(color_scheme, "Color scheme", "color_scheme")

    def set_viewer(self, viewer):
        """Attach the events to the viewer."""
        self.viewer = viewer
        # volume_visibility_checked = self.getWidget("volume_visibility").checkState()
        # if volume_visibility_checked:

        self.getWidget("volume_visibility").stateChanged.connect(self.toggle_volume_visibility)
        self.getWidget("opacity_mapping").currentIndexChanged.connect(self.change_opacity_mapping)

    def change_opacity_mapping(self):
        method = self.getWidget("opacity_mapping").currentText().lower()
        self.viewer.setVolumeRenderOpacityMethod(method)
        self.viewer.updateVolumePipeline()

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
        self.viewer.style.ToggleVolumeVisibility()
        self.change_opacity_mapping()
        self.viewer.updateVolumePipeline()
