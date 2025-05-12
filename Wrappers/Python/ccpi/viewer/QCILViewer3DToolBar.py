from PySide2 import QtWidgets, QtCore

from ccpi.viewer.utils.settings_tooltips import TOOLTIPS_3D_TOOLBAR
from ccpi.viewer.ui.SettingsDialog import SettingsDialog
from ccpi.viewer.ui.VolumeRenderSettingsDialog import VolumeRenderSettingsDialog
from ccpi.viewer.ui.CameraSettingsDialog import CameraSettingsDialog


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

        super(QCILViewer3DToolBar, self).__init__(parent=self.parent)
        self.dialog = {"settings_2d": None, "settings_3d": None, "settings_camera": None}

        # Settings Menu
        viewer_menu = QtWidgets.QMenu(parent=self)

        viewer_menu_button = QtWidgets.QToolButton(parent=self)
        viewer_menu_button.setText("3D Viewer")
        viewer_menu_button.setMenu(viewer_menu)
        viewer_menu_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        viewer_menu_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        viewer_menu_button.setToolTip(TOOLTIPS_3D_TOOLBAR["viewer_menu_button"])

        settings_2d = QtWidgets.QAction("Slice Settings", parent=self)
        settings_2d.triggered.connect(lambda: self.open_dialog("settings_2d"))
        viewer_menu.addAction(settings_2d)

        settings_3d = QtWidgets.QAction("Volume Render Settings", parent=self)
        settings_3d.triggered.connect(lambda: self.open_dialog("settings_3d"))
        viewer_menu.addAction(settings_3d)

        self.addWidget(viewer_menu_button)

        # camera Menu
        camera_menu = QtWidgets.QMenu(parent=self)

        camera_menu_button = QtWidgets.QToolButton(parent=self)
        camera_menu_button.setText("Camera")
        camera_menu_button.setMenu(camera_menu)
        camera_menu_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        camera_menu_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        camera_menu_button.setToolTip(TOOLTIPS_3D_TOOLBAR["camera_menu_button"])

        settings_camera = QtWidgets.QAction("Camera Settings", parent=self)
        settings_camera.triggered.connect(lambda: self.open_dialog("settings_camera"))
        camera_menu.addAction(settings_camera)

        self.addWidget(camera_menu_button)

    def open_dialog(self, mode):
        """Open a dialog box for the settings of the viewer."""
        if mode == "settings_2d":
            if self.dialog["settings_2d"] is None:
                dialog = SettingsDialog(parent=self.parent, title="Slice Settings")
                dialog.Ok.clicked.connect(lambda: self.accepted(mode))
                dialog.Cancel.clicked.connect(lambda: self.rejected(mode))
                dialog.set_viewer(self.viewer)
                self.dialog[mode] = dialog
            self.settings = self.dialog[mode].get_settings()
            self.dialog[mode].open()
            return

        if mode == "settings_3d":
            if self.dialog["settings_3d"] is None:
                dialog = VolumeRenderSettingsDialog(parent=self.parent,
                                                    title="Volume Render Settings")
                dialog.Ok.clicked.connect(lambda: self.accepted(mode))
                dialog.Cancel.clicked.connect(lambda: self.rejected(mode))
                dialog.set_viewer(self.viewer)
                self.dialog[mode] = dialog
            self.settings = self.dialog[mode].get_settings()
            self.dialog[mode].open()
            return
        
        if mode == "settings_camera":
            if self.dialog["settings_camera"] is None:
                dialog = CameraSettingsDialog(parent=self.parent,
                                                    title="Camera Settings")
                dialog.Ok.clicked.connect(lambda: self.accepted(mode))
                dialog.Cancel.clicked.connect(lambda: self.rejected(mode))
                dialog.set_viewer(self.viewer)
                self.dialog[mode] = dialog
            self.settings = self.dialog[mode].get_settings()
            self.dialog[mode].open()

    def accepted(self, mode):
        """Extract settings and apply them."""
        self.dialog[mode].close()

    def rejected(self, mode):
        """Reapply previous settings."""
        self.dialog[mode].apply_settings(self.settings)
        self.dialog[mode].close()

    def update_dialog(self):
        pass

