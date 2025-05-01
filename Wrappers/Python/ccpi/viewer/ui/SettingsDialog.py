import os

from eqt.ui import FormDialog, UISliderWidget
from PySide2 import QtCore, QtWidgets

try:
    import vtkmodules.all as vtk
    # from vtkmodules.util import colors
except ImportError:
    import vtk
from vtk.util import colors

from ccpi.viewer.utils.tooltips import TOOLTIPS_IMAGE_SETTINGS
from ccpi.viewer.ui.helpers import background_color_list


class SettingsDialog(FormDialog):
    """
    Image settings dialog.
    """

    def __init__(self, parent=None, title=None, scale_factor=1):
        FormDialog.__init__(self, parent=parent, title=title)
        print(parent)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.scale_factor = scale_factor
        self.file_location = "."

        # Background Colour
        background_colour = QtWidgets.QComboBox(self.groupBox)
        for i in background_color_list():
            background_colour.addItem(i["text"])
        self.addWidget(background_colour, "Background Colour:", "background_colour")
        self.formWidget.widgets["background_colour_label"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["background_colour"])

        # Image Orientation
        orientation = QtWidgets.QComboBox(self.groupBox)
        orientation.addItems(["YZ", "XZ", "XY"])
        orientation.setCurrentIndex(2)
        self.addWidget(orientation, "Orientation:", "orientation")
        self.formWidget.widgets["orientation_label"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["orientation"])

        # Image Visibility
        image_visibility = QtWidgets.QCheckBox("Image Visibility", self.groupBox)
        self.addWidget(image_visibility, "", "image_visibility")
        self.formWidget.widgets["image_visibility_field"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["image_visibility"])

        # Auto Window/Level
        auto_window_level = QtWidgets.QPushButton("Auto Window/Level")
        self.addWidget(auto_window_level, "", "auto_window_level")
        self.formWidget.widgets["auto_window_level_field"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["auto_window_level"])

        # Image Window Sliders
        image_window_slider = UISliderWidget.UISliderWidget(0.0, 255.0)
        self.addWidget(image_window_slider, "Image Window:", "image_window_slider")
        self.formWidget.widgets["image_window_slider_label"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["image_window_slider"])

        # Image Level Sliders
        image_level_slider = UISliderWidget.UISliderWidget(0.0, 255.0)
        self.addWidget(image_level_slider, "Image Level:", "image_level_slider")
        self.formWidget.widgets["image_level_slider_label"].setToolTip(TOOLTIPS_IMAGE_SETTINGS["image_level_slider"])

        # Render Save Location
        render_save_location = QtWidgets.QLabel("'render'")
        open_location_browser = QtWidgets.QPushButton("Open Location Browser")
        self.addWidget(render_save_location, "Render Save Location:", "render_save_location")
        self.addWidget(open_location_browser, "", "open_location_browser")
        self.formWidget.widgets["render_save_location_label"].setToolTip(
            TOOLTIPS_IMAGE_SETTINGS["render_save_location"])
        self.formWidget.widgets["open_location_browser_field"].setToolTip(
            TOOLTIPS_IMAGE_SETTINGS["open_location_browser"])

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
        self.getWidget("image_window_slider").setValue(window_default)

        level_default = self.viewer.getSliceColorLevel()
        self.getWidget("image_level_slider").setValue(level_default)

    def set_viewer(self, viewer):
        """Attach the events to the viewer."""
        self.viewer = viewer

        # Orientation
        self.getWidget("orientation").currentIndexChanged.connect(self.change_viewer_orientation)

        # Image Visibility
        self.getWidget("image_visibility").setChecked(True)
        self.getWidget("image_visibility").stateChanged.connect(self.viewer.style.ToggleSliceVisibility)

        # Auto Window/Level
        self.getWidget("auto_window_level").clicked.connect(self.auto_window_level)

        # Image Window Sliders
        window_min, window_max = self.viewer.getImageMapRange((0.0, 1.0), "scalar")
        window_default = self.viewer.getSliceColorWindow()

        self.getWidget("image_window_slider").setValue(window_default)
        self.getWidget("image_window_slider").slider.valueChanged.connect(lambda: self.viewer.setSliceColorWindow(
            window_min + self.getWidget("image_window_slider").value() / 100 * (window_max - window_min)))
        self.getWidget("image_window_slider").line_edit.editingFinished.connect(lambda: self.viewer.setSliceColorWindow(
            window_min + self.getWidget("image_window_slider").value() / 100 * (window_max - window_min)))

        # Level Window Sliders
        level_min, level_max = self.viewer.getImageMapRange((0.0, 1.0), "scalar")
        level_default = self.viewer.getSliceColorLevel()

        self.getWidget("image_level_slider").setValue(level_default)
        self.getWidget("image_level_slider").slider.valueChanged.connect(lambda: self.viewer.setSliceColorLevel(
            level_min + self.getWidget("image_level_slider").value() / 100 * (level_max - level_min)))
        self.getWidget("image_level_slider").line_edit.editingFinished.connect(lambda: self.viewer.setSliceColorLevel(
            level_min + self.getWidget("image_level_slider").value() / 100 * (level_max - level_min)))

        # Background Colour
        self.getWidget("background_colour").currentIndexChanged.connect(self.change_background_colour)

        # Render Save Location
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

    def change_background_colour(self):
        """Change the background colour."""
        color = self.getWidget("background_colour").currentText().replace(" ", "_").lower()
        if color == "miles_blue":
            color_data = (0.1, 0.2, 0.4)
        else:
            color_data = getattr(colors, color.lower())
        self.viewer.ren.SetBackground(color_data)
        self.viewer.updatePipeline()

    def adjust_slider(self, value):
        pass
