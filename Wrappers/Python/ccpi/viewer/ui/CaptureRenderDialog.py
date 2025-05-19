import os

from eqt.ui import FormDialog, UISliderWidget
from PySide2 import QtCore, QtGui, QtWidgets

try:
    import vtkmodules.all as vtk
    # from vtkmodules.util import colors
except ImportError:
    import vtk

from ccpi.viewer.utils.settings_tooltips import TOOLTIPS_CAPTURE_RENDER


class CaptureRenderDialog(FormDialog):
    """
    Capture render dialog.
    """

    def __init__(self, parent=None, viewer=None, title=None):
        FormDialog.__init__(self, parent=parent, title=title)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.viewer = viewer

        self.default_filename = "current_render"
        self.file_location = os.getcwd()
        self.custom_file_location = os.getcwd()

        self._setUpRenderSaveFilename()
        self._setUpRenderSaveLocation()
        self._setUpOpenLocationBrowser()
        self._setUpCaptureRender()

    def _setUpRenderSaveLocation(self):
        render_save_location = QtWidgets.QLabel(f"\\{os.path.basename(self.file_location)}")

        self.addWidget(render_save_location, "Save Location:", "render_save_location")
        self.formWidget.widgets["render_save_location_label"].setToolTip(
            TOOLTIPS_CAPTURE_RENDER["render_save_location"])
        self.formWidget.widgets["render_save_location_field"].setToolTip(render_save_location.text())

    def _setUpOpenLocationBrowser(self):
        open_location_browser = QtWidgets.QPushButton("Open Location Browser")

        self.addWidget(open_location_browser, "", "open_location_browser")
        self.formWidget.widgets["open_location_browser_field"].setToolTip(
            TOOLTIPS_CAPTURE_RENDER["open_location_browser"])

        self.getWidget("open_location_browser").clicked.connect(self.openFileLocationDialog)

    def _setUpRenderSaveFilename(self):
        regex = QtCore.QRegExp(r"^.[^\/:*?\"<>|]+$")

        validator = QtGui.QRegExpValidator()
        validator.setRegExp(regex)
        validator.setLocale(QtCore.QLocale("en_US"))

        render_save_filename = QtWidgets.QLineEdit()
        render_save_filename.setValidator(validator)
        render_save_filename.setText(self.default_filename)
        render_save_filename.setClearButtonEnabled(True)
        render_save_filename.setPlaceholderText(self.default_filename)

        self.addWidget(render_save_filename, "Filename:", "render_save_filename")
        self.formWidget.widgets["render_save_filename_label"].setToolTip(
            TOOLTIPS_CAPTURE_RENDER["render_save_filename"])

    def _setUpCaptureRender(self):
        self.getWidgetFromVerticalLayout(1).buttons()[0].setText("Capture Render")
        self.getWidgetFromVerticalLayout(1).buttons()[0].setToolTip(TOOLTIPS_CAPTURE_RENDER["capture_render"])

    def onOk(self):
        self.saveRender()

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
            elif isinstance(value, QtWidgets.QLineEdit):
                settings[key] = value.text()

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
            elif isinstance(value, QtWidgets.QLineEdit):
                widg.setText(value)

    def openFileLocationDialog(self):
        """Open file location dialog."""
        dialog = QtWidgets.QFileDialog()
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        self.custom_file_location = dialog.getExistingDirectory(self, caption="Select Folder", dir=self.file_location)
        # relative_filepath = (os.path.relpath(self.custom_file_location, os.getcwd()))
        self.getWidget("render_save_location").setText(f"'{os.path.basename(self.custom_file_location)}'")
        self.formWidget.widgets["render_save_location_field"].setToolTip(self.custom_file_location)

    def saveRender(self):
        """Save the render to a file."""
        filename = self.getWidget("render_save_filename").text()
        if filename == "":
            file_path = os.path.join(self.custom_file_location, self.default_filename)
        else:
            file_path = os.path.join(self.custom_file_location, filename)
        self.viewer.saveRender(file_path)
        print(f"Render saved: {file_path}")
