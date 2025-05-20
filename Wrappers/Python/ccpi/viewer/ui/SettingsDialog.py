from eqt.ui import FormDialog, UISliderWidget
from PySide2 import QtCore, QtWidgets

from ccpi.viewer import (SLICE_ORIENTATION_XY, SLICE_ORIENTATION_XZ, SLICE_ORIENTATION_YZ)
from vtk.util import colors

from ccpi.viewer.utils.settings_tooltips import TOOLTIPS_IMAGE_SETTINGS
from ccpi.viewer.ui.helpers import background_color_list


class SettingsDialog(FormDialog):
    """
    A FormDialog listing the viewer's slice settings.
    """

    def __init__(self, parent=None, viewer=None, title=None):
        """
        Creates the FormDialog and sets up the form's widgets.
        The widgets are enabled if image data has been loaded in the viewer.
        Otherwise, the widgets are disabled. 

        viewer: The CILViewer instance that the dialog's settings will connect to.
        """
        FormDialog.__init__(self, parent=parent, title=title)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.viewer = viewer

        self.default_slider_min = 0.0
        self.default_slider_max = 255.0

        self._setUpBackgroundColour()
        self._setUpSliceVisibility()
        self._setUpSliceOrientation()
        self._setUpAutoWindowLevel()
        self._setUpSliceWindow()
        self._setUpSliceLevel()

        self.toggleSliceVisibility(is_init=True)

    def _setUpBackgroundColour(self):
        """
        Configures the Background Colour QComboBox, which controls the background colour of the viewer.
        """
        background_colour = QtWidgets.QComboBox(self.groupBox)
        for i in background_color_list():
            background_colour.addItem(i["text"])

        self.addWidget(background_colour, "Background Colour:", "background_colour")
        self.formWidget.widgets["background_colour_label"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["background_colour"])

        self.getWidget("background_colour").currentIndexChanged.connect(self.setBackgroundColour)

    def _setUpSliceVisibility(self):
        """
        Configures the Slice Visibility QCheckBox, which both controls the visibility of the slice and
        enables/disables the dialog's settings widgets.

        If no image data has been loaded in the viewer, the QCheckBox will be unticked and disabled.
        """
        slice_visibility = QtWidgets.QCheckBox("Slice Visibility", self.groupBox)

        self.addWidget(slice_visibility, "", "slice_visibility")
        self.formWidget.widgets["slice_visibility_field"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["slice_visibility"])

        if self.viewer.img3D is None:
            self.getWidget("slice_visibility").setChecked(False)
            self.getWidget("slice_visibility").setEnabled(False)
        else:
            self.getWidget("slice_visibility").setChecked(True)

        self.getWidget("slice_visibility").stateChanged.connect(self.toggleSliceVisibility)

    def _setUpSliceOrientation(self):
        """
        Configures the Orientation QComboBox, which controls the orientation of slice in the viewer.
        The QComboBox is populated with the axis labels that have been set in the viewer. 
        By default, sets the default orientation to index 2 in the list. 
        """
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

        self.getWidget("orientation").currentIndexChanged.connect(self.setViewerOrientation)

    def _setUpAutoWindowLevel(self):
        """
        Configures the Auto Window/Level QButton, which sets the viewer and the window/level sliders
        to the slice's default window/level values.
        """
        auto_window_level = QtWidgets.QPushButton("Auto Window/Level")

        self.addWidget(auto_window_level, "", "auto_window_level")
        self.formWidget.widgets["auto_window_level_field"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["auto_window_level"])

        self.getWidget("auto_window_level").clicked.connect(self.setAutoWindowLevel)

    def _setUpSliceWindow(self):
        """
        Configures the Slice Window slider, which controls the range of grey scale values the slice will display.
        If image data is loaded, the slider's min/max values are derived from the viewer's image map range.
        Otherwise, the slider's min/max values are set to the "default_slider_min/max" attributes. 
        """
        window_min, window_max = self.viewer.getImageMapRange((0.0, 100.0), "scalar")
        window_default = self.viewer.getSliceColorWindow()

        if self.viewer.img3D is None:
            slice_window_slider = UISliderWidget.UISliderWidget(self.default_slider_min, self.default_slider_max)
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
        """
        Configures the Slice Level slider, which controls the central point of the grey scale value range.
        If image data is loaded, the slider's min/max values are derived from the viewer's image map range.
        Otherwise, the slider's min/max values are set to the "default_slider_min/max" attributes. 
        """
        level_min, level_max = self.viewer.getImageMapRange((0.0, 100.0), "scalar")
        level_default = self.viewer.getSliceColorLevel()

        if self.viewer.img3D is None:
            slice_level_slider = UISliderWidget.UISliderWidget(self.default_slider_min, self.default_slider_max)
        else:
            slice_level_slider = UISliderWidget.UISliderWidget(level_min, level_max)

        self.addWidget(slice_level_slider, "Slice Level:", "slice_level_slider")
        self.formWidget.widgets["slice_level_slider_label"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["slice_level_slider"])

        self.getWidget("slice_level_slider").setValue(level_default)
        self.getWidget("slice_level_slider").slider.valueChanged.connect(
            lambda: self.viewer.setSliceColorLevel(self.getWidget("slice_level_slider").value()))
        self.getWidget("slice_level_slider").line_edit.editingFinished.connect(
            lambda: self.viewer.setSliceColorLevel(self.getWidget("slice_level_slider").value()))

    def setAutoWindowLevel(self):
        """
        Sets the viewer and the window/level sliders to the default window/level values.
        """
        self.viewer.autoWindowLevelOnSliceRange()

        window_default = self.viewer.getSliceColorWindow()
        self.getWidget("slice_window_slider").setValue(window_default)

        level_default = self.viewer.getSliceColorLevel()
        self.getWidget("slice_level_slider").setValue(level_default)

    def setViewerOrientation(self):
        """
        Sets the viewer's orientation.
        """
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

    def setBackgroundColour(self):
        """
        Sets the viewer's background colour.
        """
        color = self.getWidget("background_colour").currentText().replace(" ", "_").lower()
        if color == "miles_blue":
            color_data = (0.1, 0.2, 0.4)
        else:
            color_data = getattr(colors, color.lower())
        self.viewer.ren.SetBackground(color_data)
        self.viewer.updatePipeline()

    def toggleSliceVisibility(self, is_init=False):
        """
        Toggles the slice visibility in the viewer. The slice visibility QCheckBox
        determines whether the dialog's widgets are enabled/disabled.

        is_init: Boolean value that limits the method's behaviour when the dialog is created.
        """
        slice_visibility_checked = self.getWidget("slice_visibility").isChecked()

        self.getWidget("orientation").setEnabled(slice_visibility_checked)
        self.getWidget("auto_window_level").setEnabled(slice_visibility_checked)
        self.getWidget("slice_window_slider").setEnabled(slice_visibility_checked)
        self.getWidget("slice_level_slider").setEnabled(slice_visibility_checked)

        if is_init is True:
            return
        else:
            self.viewer.style.ToggleSliceVisibility()

    def getSettings(self):
        """
        Returns a dictionary of widget settings from the dialog.
        """
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
        """
        Applies the widget settings to the dialog.

        settings: A dictionary of widget names and their associated state/value.
        """
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
