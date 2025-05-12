import os

from eqt.ui import FormDialog, UISliderWidget
from PySide2 import QtCore, QtWidgets

try:
    import vtkmodules.all as vtk
    # from vtkmodules.util import colors
except ImportError:
    import vtk

from ccpi.viewer.utils.settings_tooltips import TOOLTIPS_CAMERA_SETTINGS


class CameraSettingsDialog(FormDialog):
    """
    Camera settings dialog.
    """

    def __init__(self, parent=None, title=None):
        FormDialog.__init__(self, parent=parent, title=title)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)

        # Render Save Location
        render_save_location = QtWidgets.QLabel(f"{os.path.basename(os.getcwd())}")
        open_location_browser = QtWidgets.QPushButton("Open Location Browser")
        self.addWidget(render_save_location, "Render Save Location:", "render_save_location")
        self.addWidget(open_location_browser, "", "open_location_browser")
        self.formWidget.widgets["render_save_location_label"].setToolTip(
            TOOLTIPS_CAMERA_SETTINGS["render_save_location"])
        self.formWidget.widgets["open_location_browser_field"].setToolTip(
            TOOLTIPS_CAMERA_SETTINGS["open_location_browser"])

        # Save Render
        save_render = QtWidgets.QPushButton("Save Render")
        self.addWidget(save_render, "", "save_render")
        self.formWidget.widgets["save_render_field"].setToolTip(TOOLTIPS_CAMERA_SETTINGS["save_render"])

        # Reset Camera
        reset_camera = QtWidgets.QPushButton("Reset Camera")
        self.addWidget(reset_camera, "", "reset_camera")
        self.formWidget.widgets["reset_camera_field"].setToolTip(TOOLTIPS_CAMERA_SETTINGS["reset_camera"])

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

    def set_viewer(self, viewer):
        """Attach the events to the viewer."""
        self.viewer = viewer

        # Render Save Location
        self.getWidget("open_location_browser").clicked.connect(self.open_file_location_dialog)

        # Save Render
        self.getWidget("save_render").clicked.connect(self.save_render)

        # Reset Camera
        self.getWidget("reset_camera").clicked.connect(self.reset_camera)

    def open_file_location_dialog(self):
        """Open file location dialog."""
        dialog = QtWidgets.QFileDialog()
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        self.file_location = dialog.getSaveFileName(self, caption="Select File")[0]

        self.getWidget("render_save_location").setText(f"'{os.path.relpath(self.file_location, os.getcwd())}'")

    def save_render(self):
        """Save the render to a file."""
        if self.file_location is None:
            print(self.file_location)
            self.viewer.saveRender(os.get_cwd())
            print(f"Render saved: {os.get_cwd()}")
        else:
            print(self.file_location)
            self.viewer.saveRender(os.path.relpath(self.file_location, os.getcwd()))
            print(f"Render saved: {os.path.relpath(self.file_location, os.getcwd())}")

    def reset_camera(self):
        """Reset camera to default position."""
        self.viewer.resetCameraToDefault()
        self.viewer.updatePipeline()
