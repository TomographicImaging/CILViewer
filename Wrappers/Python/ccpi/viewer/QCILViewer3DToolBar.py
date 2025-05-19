from PySide2 import QtWidgets, QtCore

from ccpi.viewer.utils.settings_tooltips import TOOLTIPS_3D_TOOLBAR
from ccpi.viewer.ui.SettingsDialog import SettingsDialog
from ccpi.viewer.ui.VolumeRenderSettingsDialog import VolumeRenderSettingsDialog
from ccpi.viewer.ui.CaptureRenderDialog import CaptureRenderDialog


class QCILViewer3DToolBar(QtWidgets.QToolBar):

    def __init__(self, parent=None, viewer=None):
        """
        Parameters
        -----------
        viewer: an instance of viewer2D or viewer3D
            the viewer which the toolbar is for. The viewer instance
            is passed to allow interactions to be controlled using the
            toolbar.
        """

        self.parent = parent
        self.viewer = viewer

        if self.viewer.img3D is None:
            self.data = None
        else:
            self.data = viewer.img3D

        super(QCILViewer3DToolBar, self).__init__(parent=self.parent)
        self.dialog = {"settings_2d": None, "settings_3d": None, "settings_render": None}

        self._setUpSettingsMenu()
        self._setUpCameraMenu()

    def _setUpSettingsMenu(self):
        viewer_menu = QtWidgets.QMenu(parent=self)

        viewer_menu_button = QtWidgets.QToolButton(parent=self)
        viewer_menu_button.setText("3D Viewer")
        viewer_menu_button.setMenu(viewer_menu)
        viewer_menu_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        viewer_menu_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        viewer_menu_button.setToolTip(TOOLTIPS_3D_TOOLBAR["viewer_menu_button"])

        settings_2d = QtWidgets.QAction("Slice Settings", parent=self)
        settings_2d.triggered.connect(lambda: self.openDialog("settings_2d"))
        viewer_menu.addAction(settings_2d)

        settings_3d = QtWidgets.QAction("Volume Render Settings", parent=self)
        settings_3d.triggered.connect(lambda: self.openDialog("settings_3d"))
        viewer_menu.addAction(settings_3d)

        self.addWidget(viewer_menu_button)

    def _setUpCameraMenu(self):
        camera_menu = QtWidgets.QMenu(parent=self)

        camera_menu_button = QtWidgets.QToolButton(parent=self)
        camera_menu_button.setText("Camera")
        camera_menu_button.setMenu(camera_menu)
        camera_menu_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        camera_menu_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        camera_menu_button.setToolTip(TOOLTIPS_3D_TOOLBAR["camera_menu_button"])

        resetCamera = QtWidgets.QAction("Reset Camera", parent=self)
        resetCamera.triggered.connect(self.resetCamera)
        camera_menu.addAction(resetCamera)

        settings_render = QtWidgets.QAction("Capture Render", parent=self)
        settings_render.triggered.connect(lambda: self.openDialog("settings_render"))
        camera_menu.addAction(settings_render)

        self.addWidget(camera_menu_button)

    def openDialog(self, mode):
        """Open a dialog box for the settings of the viewer."""
        if self._isNewData(self.viewer.img3D):
            self._createSettingsDialog()
            self._createVolumeRenderSettingsDialog()

        if mode == "settings_2d":
            if self.dialog["settings_2d"] is None:
                self._createSettingsDialog()
            self.settings = self.dialog[mode].getSettings()
            self.dialog[mode].open()
            return

        if mode == "settings_3d":
            if self.dialog["settings_3d"] is None:
                self._createVolumeRenderSettingsDialog()
            self.settings = self.dialog[mode].getSettings()
            self.dialog[mode].open()
            return

        if mode == "settings_render":
            if self.dialog["settings_render"] is None:
                self._createCaptureRenderDialog()
            self.settings = self.dialog[mode].getSettings()
            self.dialog[mode].open()
            return

    def _createSettingsDialog(self):
        mode = "settings_2d"
        dialog = SettingsDialog(parent=self.parent, viewer=self.viewer, title="Slice Settings")
        dialog.Ok.clicked.connect(lambda: self.accepted(mode))
        dialog.Cancel.clicked.connect(lambda: self.rejected(mode))
        self.dialog[mode] = dialog

    def _createVolumeRenderSettingsDialog(self):
        mode = "settings_3d"
        dialog = VolumeRenderSettingsDialog(parent=self.parent, viewer=self.viewer, title="Volume Render Settings")
        dialog.Ok.clicked.connect(lambda: self.accepted(mode))
        dialog.Cancel.clicked.connect(lambda: self.rejected(mode))
        self.dialog[mode] = dialog

    def _createCaptureRenderDialog(self):
        mode = "settings_render"
        dialog = CaptureRenderDialog(parent=self.parent, viewer=self.viewer, title="Capture Render")
        dialog.Ok.clicked.connect(lambda: self.accepted(mode))
        dialog.Cancel.clicked.connect(lambda: self.rejected(mode))
        self.dialog[mode] = dialog

    def _isNewData(self, data):
        """Checks whether the """
        if data != self.data:
            self.data = data
            return True
        else:
            return False

    def resetCamera(self):
        """Reset camera to default position."""
        self.viewer.resetCameraToDefault()

        if self.viewer.img3D is None:
            return
        else:
            self.viewer.updatePipeline()

    def accepted(self, mode):
        """Extract settings and apply them."""
        self.dialog[mode].close()

    def rejected(self, mode):
        """Reapply previous settings."""
        self.dialog[mode].applySettings(self.settings)
        self.dialog[mode].close()