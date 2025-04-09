from PySide2 import QtWidgets, QtCore

from ccpi.viewer.utils.tooltips import TOOLTIPS_3D_TOOLBAR
from ccpi.viewer.ui.SettingsDialog import SettingsDialog
from ccpi.viewer.ui.VolumeRenderSettingsDialog import VolumeRenderSettingsDialog


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

        super(QCILViewer3DToolBar, self).__init__(parent=parent)
        self.dialog = {"settings_2d": None, "settings_3d": None}

        # Settings Menu
        settings_menu = QtWidgets.QMenu(self)

        settings_button = QtWidgets.QToolButton()
        settings_button.setText("3D View Settings")
        settings_button.setMenu(settings_menu)
        settings_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        settings_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        settings_button.setToolTip(TOOLTIPS_3D_TOOLBAR["settings_button"])

        settings_2d = QtWidgets.QAction("Image Settings", self)
        settings_2d.triggered.connect(lambda: self.open_dialog("settings_2d"))
        settings_menu.addAction(settings_2d)

        settings_3d = QtWidgets.QAction("Volume Render Settings", self)
        settings_3d.triggered.connect(lambda: self.open_dialog("settings_3d"))
        settings_menu.addAction(settings_3d)

        self.addWidget(settings_button)

        # Camera Button
        camera_button = QtWidgets.QToolButton()
        camera_button.setText("Screenshot Settings")
        camera_button.setToolTip(TOOLTIPS_3D_TOOLBAR["camera_button"])

        self.addWidget(camera_button)


    def open_dialog(self, mode):
        """Open a dialog box for the settings of the viewer."""
        if mode == "settings_2d":
            if self.dialog["settings_2d"] is None:
                dialog = SettingsDialog(parent=self.parent, title="Image Settings", scale_factor=self.scale_factor)
                dialog.Ok.clicked.connect(lambda: self.accepted(mode))
                dialog.Cancel.clicked.connect(lambda: self.rejected(mode))
                dialog.set_viewer(self.viewer)
                self.dialog[mode] = dialog
                # self.default_settings = self.dialog[mode].get_settings()

            self.settings = self.dialog[mode].get_settings()
            self.dialog[mode].open()
            return
        
        if mode == "settings_3d":
            if self.dialog["settings_3d"] is None:
                dialog = VolumeRenderSettingsDialog(parent=self.parent,
                                                    title="Volume Render Settings",
                                                    scale_factor=self.scale_factor)
                dialog.Ok.clicked.connect(lambda: self.accepted(mode))
                dialog.Cancel.clicked.connect(lambda: self.rejected(mode))
                dialog.set_viewer(self.viewer)
                self.dialog[mode] = dialog

            self.settings = self.dialog[mode].get_settings()
            self.dialog[mode].open()
            return

    def accepted(self, mode):
        """Extract settings and apply them."""
        self.dialog[mode].close()

    def rejected(self, mode):
        """Reapply previous settings."""
        self.dialog[mode].apply_settings(self.settings)
        self.dialog[mode].close()

    def save_dialog_settings(self):
        pass

    def apply_dialog_settings(self, mode, settings):
        pass
