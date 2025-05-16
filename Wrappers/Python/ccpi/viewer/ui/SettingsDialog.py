from eqt.ui import FormDialog, UISliderWidget
from PySide2 import QtCore, QtWidgets

from ccpi.viewer import (SLICE_ORIENTATION_XY, SLICE_ORIENTATION_XZ, SLICE_ORIENTATION_YZ)
from vtk.util import colors

from ccpi.viewer.utils.settings_tooltips import TOOLTIPS_IMAGE_SETTINGS
from ccpi.viewer.ui.helpers import background_color_list


class SettingsDialog(FormDialog):
    """
    Slice settings dialog.
    """

    def __init__(self, parent=None, viewer=None, title=None):
        FormDialog.__init__(self, parent=parent, title=title)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.viewer = viewer

        self._setUpBackgroundColour()
        self._setUpSliceVisibility()
        self._setUpSliceOrientation()
        self._setUpAutoWindowLevel()
        self._setUpSliceWindow()
        self._setUpSliceLevel()

        self.toggleSliceVisibility(is_init=True)

    def _setUpBackgroundColour(self):
        background_colour = QtWidgets.QComboBox(self.groupBox)
        for i in background_color_list():
            background_colour.addItem(i["text"])

        self.addWidget(background_colour, "Background Colour:", "background_colour")
        self.formWidget.widgets["background_colour_label"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["background_colour"])

        self.getWidget("background_colour").currentIndexChanged.connect(self.changeBackgroundColour)

    def _setUpSliceVisibility(self):
        slice_visibility = QtWidgets.QCheckBox("Slice Visibility", self.groupBox)
        slice_visibility.setChecked(True)

        self.addWidget(slice_visibility, "", "slice_visibility")
        self.formWidget.widgets["slice_visibility_field"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["slice_visibility"])

        self.getWidget("slice_visibility").setChecked(True)
        self.getWidget("slice_visibility").stateChanged.connect(self.toggleSliceVisibility)

    def _setUpSliceOrientation(self):
        orientation = QtWidgets.QComboBox(self.groupBox)
        axis_labels = self.viewer.getCurrentAxisLabelsText()
        orientation_items = [
            f"{axis_labels[1]}-{axis_labels[2]}", f"{axis_labels[0]}-{axis_labels[2]}",
            f"{axis_labels[0]}-{axis_labels[1]}"
        ]
        orientation.addItems(orientation_items)
        orientation.setCurrentIndex(2)

        self.addWidget(orientation, "Orientation:", "orientation")
        self.formWidget.widgets["orientation_label"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["orientation"])

        self.getWidget("orientation").currentIndexChanged.connect(self.changeViewerOrientation)

    def _setUpAutoWindowLevel(self):
        auto_window_level = QtWidgets.QPushButton("Auto Window/Level")

        self.addWidget(auto_window_level, "", "auto_window_level")
        self.formWidget.widgets["auto_window_level_field"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["auto_window_level"])

        self.getWidget("auto_window_level").clicked.connect(self.applyAutoWindowLevel)

    def _setUpSliceWindow(self):
        window_min, window_max = self.viewer.getImageMapRange((0.0, 100.0), "scalar")
        window_default = self.viewer.getSliceColorWindow()

        if self.viewer.img3D is None:
            slice_window_slider = UISliderWidget.UISliderWidget(0.0, 255.0)
        else:
            slice_window_slider = UISliderWidget.UISliderWidget(window_min, window_max)

        self.addWidget(slice_window_slider, "Slice Window:", "slice_window_slider")
        self.formWidget.widgets["slice_window_slider_label"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["slice_window_slider"])

        self.getWidget("slice_window_slider").setValue(window_default)
        self.getWidget("slice_window_slider").slider.valueChanged.connect(
            lambda: self.viewer.setSliceColorWindow(self.getWidget("slice_window_slider").value()))
        self.getWidget("slice_window_slider").line_edit.editingFinished.connect(
            lambda: self.viewer.setSliceColorWindow(self.getWidget("slice_window_slider").value()))

    def _setUpSliceLevel(self):
        level_min, level_max = self.viewer.getImageMapRange((0.0, 100.0), "scalar")
        level_default = self.viewer.getSliceColorLevel()

        if self.viewer.img3D is None:
            slice_level_slider = UISliderWidget.UISliderWidget(0.0, 255.0)
        else:
            slice_level_slider = UISliderWidget.UISliderWidget(level_min, level_max)

        self.addWidget(slice_level_slider, "Slice Level:", "slice_level_slider")
        self.formWidget.widgets["slice_level_slider_label"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["slice_level_slider"])

        self.getWidget("slice_level_slider").setValue(level_default)
        self.getWidget("slice_level_slider").slider.valueChanged.connect(
            lambda: self.viewer.setSliceColorLevel(self.getWidget("slice_level_slider").value()))
        self.getWidget("slice_level_slider").line_edit.editingFinished.connect(
            lambda: self.viewer.setSliceColorLevel(self.getWidget("slice_level_slider").value()))

    def getSettings(self):
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

    def applySettings(self, settings):
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

    def applyAutoWindowLevel(self):
        """Set the window and level to the default values."""
        self.viewer.autoWindowLevelOnSliceRange()

        window_default = self.viewer.getSliceColorWindow()
        self.getWidget("slice_window_slider").setValue(window_default)

        level_default = self.viewer.getSliceColorLevel()
        self.getWidget("slice_level_slider").setValue(level_default)

    def changeViewerOrientation(self):
        """Change the viewer orientation."""
        index = self.getWidget("orientation").currentIndex()

        if index == 0:
            self.viewer.style.SetSliceOrientation(SLICE_ORIENTATION_YZ)
        elif index == 1:
            self.viewer.style.SetSliceOrientation(SLICE_ORIENTATION_XZ)
        elif index == 2:
            self.viewer.style.SetSliceOrientation(SLICE_ORIENTATION_XY)

        if self.viewer.img3D is None:
            return
        else:
            self.viewer.style.UpdatePipeline(resetcamera=True)

    def changeBackgroundColour(self):
        """Change the background colour."""
        color = self.getWidget("background_colour").currentText().replace(" ", "_").lower()
        if color == "miles_blue":
            color_data = (0.1, 0.2, 0.4)
        else:
            color_data = getattr(colors, color.lower())
        self.viewer.ren.SetBackground(color_data)
        self.viewer.updatePipeline()

    def toggleSliceVisibility(self, is_init=False):
        """Toggle slice visibility."""
        # Set 3D widgets enabled/disabled depending on slice visibility checkbox
        slice_visibility_checked = self.getWidget("slice_visibility").isChecked()
        self.getWidget("orientation").setEnabled(slice_visibility_checked)
        self.getWidget("auto_window_level").setEnabled(slice_visibility_checked)
        self.getWidget("slice_window_slider").setEnabled(slice_visibility_checked)
        self.getWidget("slice_level_slider").setEnabled(slice_visibility_checked)

        if is_init == True:
            return
        else:
            self.viewer.style.ToggleSliceVisibility()
