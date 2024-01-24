import os

from eqt.ui import FormDialog, UISliderWidget
from PySide2 import QtCore, QtWidgets

try:
    import vtkmodules.all as vtk
    # from vtkmodules.util import colors
except ImportError:
    import vtk
from vtk.util import colors

from ccpi.viewer.ui.helpers import background_color_list


class SettingsDialog(FormDialog):
    """Slice settings dialog."""

    def __init__(self, parent=None, title=None, scale_factor=1):
        FormDialog.__init__(self, parent, title=title)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.file_location = "."

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
        self.scale_factor = scale_factor
        slice_window_label = QtWidgets.QLabel("Slice Window")
        slice_window_slider = UISliderWidget.UISliderWidget(slice_window_label, scale_factor=1 / scale_factor)
        self.addWidget(slice_window_slider, "Slice Window", "slice_window_slider")
        self.addWidget(slice_window_label, "", "slice_window_label")

        # Slice level sliders
        slice_level_label = QtWidgets.QLabel("Slice Level")
        slice_level_slider = UISliderWidget.UISliderWidget(slice_level_label, scale_factor=1 / scale_factor)
        self.addWidget(slice_level_slider, "Slice Level", "slice_level_slider")
        self.addWidget(slice_level_label, "", "slice_level_label")

        # Render save location
        render_save_location = QtWidgets.QLabel("'render'")
        open_location_browser = QtWidgets.QPushButton("Open location browser")
        self.addWidget(render_save_location, "Render save location", "render_save_location")
        self.addWidget(open_location_browser, "", "open_location_browser")

    def get_settings(self):
        """Return a dictionary of settings from the dialog."""
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
        """Apply the settings to the dialog."""
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
        """Set the window and level to the default values."""
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
        self.getWidget("slice_visibility").setChecked(True)
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
            lambda: self.viewer.setSliceColorWindow(self.getWidget("slice_window_slider").value()))

        # Level window sliders
        level_min, level_max = self.viewer.getImageMapRange((0.0, 100.0), "scalar")
        self.getWidget("slice_level_slider").setRange(level_min, level_max)
        self.getWidget("slice_level_slider").setTickInterval((level_max - level_min) / 10)
        level_default = self.viewer.getSliceColorLevel()
        self.getWidget("slice_level_slider").setValue(level_default)
        self.getWidget("slice_level_slider").valueChanged.connect(
            lambda: self.viewer.setSliceColorLevel(self.getWidget("slice_level_slider").value()))

        # Background color
        self.getWidget("background_color").currentIndexChanged.connect(self.change_background_color)

        # Render save location
        self.getWidget("open_location_browser").clicked.connect(self.open_file_location_dialog)

    def open_file_location_dialog(self):
        """Open file location dialog."""
        dialog = QtWidgets.QFileDialog()
        self.file_location = dialog.getSaveFileName(self, "Select File")[0]

        self.getWidget("render_save_location").setText(f"'{os.path.relpath(self.file_location, os.getcwd())}'")

    def change_viewer_orientation(self):
        """Change the viewer orientation."""
        index = self.getWidget("orientation").currentIndex()
        self.viewer.style.SetSliceOrientation(index)
        self.viewer.style.UpdatePipeline(resetcamera=True)

    def change_background_color(self):
        """Change the background color."""
        color = self.getWidget("background_color").currentText().replace(" ", "_").lower()
        if color == "miles_blue":
            color_data = (0.1, 0.2, 0.4)
        else:
            color_data = getattr(colors, color.lower())
        self.viewer.ren.SetBackground(color_data)
        self.viewer.updatePipeline()

    def adjust_slider(self, value):
        pass
