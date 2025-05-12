import os

from eqt.ui import FormDialog, UISliderWidget
from PySide2 import QtCore, QtWidgets

try:
    import vtkmodules.all as vtk
    # from vtkmodules.util import colors
except ImportError:
    import vtk
from ccpi.viewer import (SLICE_ORIENTATION_XY, SLICE_ORIENTATION_XZ, SLICE_ORIENTATION_YZ)
from vtk.util import colors

from ccpi.viewer.utils.settings_tooltips import TOOLTIPS_IMAGE_SETTINGS
from ccpi.viewer.ui.helpers import background_color_list


class SettingsDialog(FormDialog):
    """
    Slice settings dialog.
    """

    def __init__(self, parent=None, title=None):
        FormDialog.__init__(self, parent=parent, title=title)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.file_location = "."

        # Background Colour
        background_colour = QtWidgets.QComboBox(self.groupBox)
        for i in background_color_list():
            background_colour.addItem(i["text"])
        self.addWidget(background_colour, "Background Colour:", "background_colour")
        self.formWidget.widgets["background_colour_label"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["background_colour"])

        # Slice Visibility
        slice_visibility = QtWidgets.QCheckBox("Slice Visibility", self.groupBox)
        slice_visibility.setChecked(True)
        self.addWidget(slice_visibility, "", "slice_visibility")
        self.formWidget.widgets["slice_visibility_field"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["slice_visibility"])

        # Slice Orientation
        orientation = QtWidgets.QComboBox(self.groupBox)
        orientation.addItems(["Y-Z", "X-Z", "X-Y"])
        orientation.setCurrentIndex(2)
        self.addWidget(orientation, "Orientation:", "orientation")
        self.formWidget.widgets["orientation_label"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["orientation"])

        # Auto Window/Level
        auto_window_level = QtWidgets.QPushButton("Auto Window/Level")
        self.addWidget(auto_window_level, "", "auto_window_level")
        self.formWidget.widgets["auto_window_level_field"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["auto_window_level"])

        # Slice Window
        slice_window_slider = UISliderWidget.UISliderWidget(0.0, 100.0)
        self.addWidget(slice_window_slider, "Slice Window:", "slice_window_slider")
        self.formWidget.widgets["slice_window_slider_label"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["slice_window_slider"])

        # Slice Level
        slice_level_slider = UISliderWidget.UISliderWidget(0.0, 100.0)
        self.addWidget(slice_level_slider, "Slice Level:", "slice_level_slider")
        self.formWidget.widgets["slice_level_slider_label"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["slice_level_slider"])

        # Disable slice-related widgets if slice visibility is not checked
        slice_visibility_checked = self.getWidget("slice_visibility").isChecked()
        self.getWidget("orientation").setEnabled(slice_visibility_checked)
        self.getWidget("auto_window_level").setEnabled(slice_visibility_checked)
        self.getWidget("slice_window_slider").setEnabled(slice_visibility_checked)
        self.getWidget("slice_level_slider").setEnabled(slice_visibility_checked)

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

        # Background Colour
        self.getWidget("background_colour").currentIndexChanged.connect(self.change_background_colour)

        # Slice Visibility
        self.getWidget("slice_visibility").setChecked(True)
        self.getWidget("slice_visibility").stateChanged.connect(self.toggle_slice_visibility)

        # Orientation
        self.getWidget("orientation").currentIndexChanged.connect(self.change_viewer_orientation)

        # Auto Window/Level
        self.getWidget("auto_window_level").clicked.connect(self.auto_window_level)

        # Slice Window Slider
        window_min, window_max = self.viewer.getSliceMapRange((0.0, 100.0), "scalar")
        window_default = self.viewer.getSliceColorWindow()

        # self.formWidget.widgets["slice_window_slider_field"] = UISliderWidget.UISliderWidget(minimum=0.0, maximum=1.0)
        self.getWidget("slice_window_slider").setValue(window_default)
        self.getWidget("slice_window_slider").slider.valueChanged.connect(
            lambda: self.viewer.setSliceColorWindow(self.getWidget("slice_window_slider").value()))
        self.getWidget("slice_window_slider").line_edit.editingFinished.connect(
            lambda: self.viewer.setSliceColorWindow(self.getWidget("slice_window_slider").value()))

        # Level Window Slider
        level_min, level_max = self.viewer.getSliceMapRange((0.0, 100.0), "scalar")
        level_default = self.viewer.getSliceColorLevel()

        # self.formWidget.widgets["slice_level_slider_field"] = UISliderWidget.UISliderWidget(minimum=level_min, maximum=level_max)
        self.getWidget("slice_level_slider").setValue(level_default)
        self.getWidget("slice_level_slider").slider.valueChanged.connect(
            lambda: self.viewer.setSliceColorLevel(self.getWidget("slice_level_slider").value()))
        self.getWidget("slice_level_slider").line_edit.editingFinished.connect(
            lambda: self.viewer.setSliceColorLevel(self.getWidget("slice_level_slider").value()))

    def change_viewer_orientation(self):
        """Change the viewer orientation."""
        index = self.getWidget("orientation").currentIndex()
        al = self.viewer.style._viewer.axisLabelsText

        if index == 0:
            self.viewer.style._viewer.setAxisLabels(['', al[1], al[2]], False)
            self.viewer.style.SetSliceOrientation(SLICE_ORIENTATION_YZ)
        elif index == 1:
            self.viewer.style._viewer.setAxisLabels([al[0], '', al[2]], False)
            self.viewer.style.SetSliceOrientation(SLICE_ORIENTATION_XZ)
        elif index == 2:
            self.viewer.style._viewer.setAxisLabels([al[0], al[1], ''], False)
            self.viewer.style.SetSliceOrientation(SLICE_ORIENTATION_XY)

        if self.viewer.img3D is None:
            return
        else:
            self.viewer.style.UpdatePipeline(resetcamera=True)

    def change_background_colour(self):
        """Change the background colour."""
        color = self.getWidget("background_colour").currentText().replace(" ", "_").lower()
        if color == "miles_blue":
            color_data = (0.1, 0.2, 0.4)
        else:
            color_data = getattr(colors, color.lower())
        self.viewer.ren.SetBackground(color_data)
        self.viewer.updatePipeline()

    def toggle_slice_visibility(self):
        """Toggle slice visibility."""
        # Set 3D widgets enabled/disabled depending on slice visibility checkbox
        slice_visibility_checked = self.getWidget("slice_visibility").isChecked()
        self.getWidget("orientation").setEnabled(slice_visibility_checked)
        self.getWidget("auto_window_level").setEnabled(slice_visibility_checked)
        self.getWidget("slice_window_slider").setEnabled(slice_visibility_checked)
        self.getWidget("slice_level_slider").setEnabled(slice_visibility_checked)

        self.viewer.style.ToggleSliceVisibility()
