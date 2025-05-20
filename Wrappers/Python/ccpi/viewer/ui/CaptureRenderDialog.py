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
    A FormDialog for the capture render dialog.
    By default, renders are saved in CILViewer's root directory with
    the filename "current_render_XXXX", where "XXXX" is a numerical suffix
    to identify duplicates starting at "0000". 

    Users can specify the filename prefix for saved renders using the QLineEdit,
    and specify the directory where the renders will be saved using "Open Location
    Browser" QButton. Clicking on this button will launch a file browser dialog,
    allowing the user to select their desired directory. 

    Clicking the "Capture Render" QButton will saved a render with the specified
    filename in the chosen save location.
    """

    def __init__(self, parent=None, viewer=None, title=None):
        """
        Creates the FormDialog and sets up the form's widgets.
        Sets the default filename used 

        viewer: The CILViewer instance that the dialog's settings will connect to.
        """
        FormDialog.__init__(self, parent=parent, title=title)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.viewer = viewer

        self.default_filename = "current_render"
        self.file_location = os.getcwd()
        self.custom_file_location = os.getcwd()

        self._setUpSaveFilename()
        self._setUpSaveLocation()
        self._setUpOpenLocationBrowser()
        self._setUpCaptureRender()

    def _setUpSaveLocation(self):
        save_location = QtWidgets.QLabel(f"\\{os.path.basename(self.file_location)}")

        self.addWidget(save_location, "Save Location:", "save_location")
        self.formWidget.widgets["save_location_label"].setToolTip(
            TOOLTIPS_CAPTURE_RENDER["save_location"])
        self.formWidget.widgets["save_location_field"].setToolTip(
            save_location.text())

    def _setUpOpenLocationBrowser(self):
        """
        Configures the Open Location Browser QButton. 
        """
        open_location_browser = QtWidgets.QPushButton("Open Location Browser")

        self.addWidget(open_location_browser, "", "open_location_browser")
        self.formWidget.widgets["open_location_browser_field"].setToolTip(
            TOOLTIPS_CAPTURE_RENDER["open_location_browser"])
        
        self.getWidget("open_location_browser").clicked.connect(self.openSaveLocationDialog)

    def _setUpSaveFilename(self):
        """
        Configures the Filename QLineEdit. Uses a QRegExp and QRegExpValidator to
        prevent illegal characters from being used in the filename.
        """
        regex = QtCore.QRegExp(r"^.[^\/:*?\"<>|]+$")

        validator = QtGui.QRegExpValidator()
        validator.setRegExp(regex)
        validator.setLocale(QtCore.QLocale("en_US"))

        save_filename = QtWidgets.QLineEdit()
        save_filename.setValidator(validator)
        save_filename.setText(self.default_filename)
        save_filename.setClearButtonEnabled(True)
        save_filename.setPlaceholderText(self.default_filename)

        self.addWidget(save_filename, "Filename:", "save_filename")
        self.formWidget.widgets["save_filename_label"].setToolTip(TOOLTIPS_CAPTURE_RENDER["save_filename"])

    def _setUpCaptureRender(self):
        """
        Configures the Capture Render QButton, which it does by overwriting the dialog's
        "Ok" QButton widget text. 
        """
        self.getWidgetFromVerticalLayout(1).buttons()[0].setText("Capture Render")
        self.getWidgetFromVerticalLayout(1).buttons()[0].setToolTip(TOOLTIPS_CAPTURE_RENDER["capture_render"])

    def onOk(self):
        """
        Redefines the FormDialog's onOK() method to call the saveRender() method when the
        Ok button (or in this case, the Capture Render button) is clicked.
        """
        self.saveRender()

    def openSaveLocationDialog(self):
        """
        Creates and opens the save location QFileDialog. Updates the "custom_file_location" 
        attribute and the QLabel's tooltip with the selected file location.
        """
        dialog = QtWidgets.QFileDialog()
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)

        self.custom_file_location = dialog.getExistingDirectory(self, caption="Select Folder", dir=self.file_location)

        self.getWidget("save_location").setText(f"'{os.path.basename(self.custom_file_location)}'")
        self.formWidget.widgets["save_location_field"].setToolTip(self.custom_file_location)

    def saveRender(self):
        """
        Saves a render of the viewer to a PNG file. Uses the "default_filename" attribute
        to name the file if no filename has been specified. Otherwise, uses the value of
        the Filename QLineEdit to name the file. 
        """
        filename = self.getWidget("save_filename").text()
        if filename == "":
            file_path = os.path.join(self.custom_file_location, self.default_filename)
        else:
            file_path = os.path.join(self.custom_file_location, filename)
        self.viewer.saveRender(file_path)
        print(f"Render saved: {file_path}")

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
            elif isinstance(value, QtWidgets.QLineEdit):
                settings[key] = value.text()

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
            elif isinstance(value, QtWidgets.QLineEdit):
                widg.setText(value)