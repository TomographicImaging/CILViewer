from PySide2 import QtWidgets, QtCore


from ccpi.viewer.ui.SettingsDialog import SettingsDialog

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
        self.dialog = {"viewer_settings": None}

        # Settings Menu
        settings_menu = QtWidgets.QMenu(self)
        viewer_settings = QtWidgets.QAction("3D Viewer Settings", self)
        settings_menu.addAction(viewer_settings)

        settings_button = QtWidgets.QToolButton()
        settings_button.setText("3D Settings")
        settings_button.setMenu(settings_menu)
        settings_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        settings_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)

        viewer_settings.triggered.connect(lambda: self.open_dialog("viewer_settings"))

        self.addWidget(settings_button)

        # Camera Button
        camera_button = QtWidgets.QToolButton()
        camera_button.setText("📷")

        self.addWidget(camera_button)


    def open_dialog(self, mode):
        """Open a dialog box for the settings of the viewer."""
        if mode == "viewer_settings":
            if self.dialog["viewer_settings"] is None:
                dialog = SettingsDialog(parent=self.parent, title="viewer_settings", scale_factor=self.scale_factor)
                dialog.Ok.clicked.connect(lambda: self.accepted(mode))
                dialog.Cancel.clicked.connect(lambda: self.rejected(mode))
                dialog.set_viewer(self.viewer)
                self.dialog[mode] = dialog
                # self.default_settings = self.dialog[mode].get_settings()

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
