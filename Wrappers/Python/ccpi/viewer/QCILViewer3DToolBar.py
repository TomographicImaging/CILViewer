from PySide2 import QtWidgets

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
        self.dialog = {"settings": None}

        # Settings Menu
        settings_2d = QtWidgets.QToolButton()
        settings_2d.setText("Settings ⚙️")
        self.addWidget(settings_2d)
        settings_2d.clicked.connect(lambda: self.open_dialog("settings"))

    def open_dialog(self, mode):
        """Open a dialog box for the settings of the viewer."""
        if mode == "settings":
            if self.dialog["settings"] is None:
                dialog = SettingsDialog(parent=self.parent, title="Settings", scale_factor=self.scale_factor)
                dialog.Ok.clicked.connect(lambda: self.accepted(mode))
                dialog.Cancel.clicked.connect(lambda: self.rejected(mode))
                dialog.set_viewer(self.viewer)
                self.dialog[mode] = dialog
                self.default_settings = self.dialog[mode].get_settings()

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
