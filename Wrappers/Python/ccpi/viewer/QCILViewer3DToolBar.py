from PySide2 import QtWidgets

from ccpi.viewer.ui.SettingsDialog import SettingsDialog
from ccpi.viewer.ui.VolumeRenderSettingsDialog import VolumeRenderSettingsDialog


class QCILViewer3DToolBar(QtWidgets.QToolBar):

    def __init__(self, parent=None, viewer=None, **kwargs):
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
        self.scale_factor = kwargs.get('scale_factor', 1.0)

        super(QCILViewer3DToolBar, self).__init__(parent=parent, **kwargs)
        self.dialog = {"settings": None, "volume_render_settings": None}

        # Settings button
        settings_2d = QtWidgets.QToolButton()
        settings_2d.setText("Settings ⚙️")
        self.addWidget(settings_2d)
        settings_2d.clicked.connect(lambda: self.open_dialog("settings"))

        # Volume render settings button
        settings_3d = QtWidgets.QToolButton()
        settings_3d.setText("Volume Render Settings ⚙️")
        self.addWidget(settings_3d)
        settings_3d.clicked.connect(lambda: self.open_dialog("volume_render_settings"))

        # Reset camera button
        settings_reset = QtWidgets.QToolButton()
        settings_reset.setText("Reset ⚙️")
        self.addWidget(settings_reset)

        # Reset settings button
        reset_camera_btn = QtWidgets.QToolButton()
        reset_camera_btn.setText("Reset 📷")
        self.addWidget(reset_camera_btn)
        reset_camera_btn.clicked.connect(self.reset_camera)

        # Save image button
        save_image = QtWidgets.QToolButton()
        save_image.setText("Save 💾")
        self.addWidget(save_image)
        save_image.clicked.connect(self.save_render)

    def reset_camera(self):
        """Reset camera to default position."""
        self.viewer.resetCameraToDefault()
        self.viewer.updatePipeline()

    def change_orientation(self, dialog):
        """Change orientation of the viewer."""
        orientation = 1
        self.viewer.style.SetSliceOrientation(orientation)
        self.viewer.updatePipeline()

    def open_dialog(self, mode):
        """Open a dialog box for the settings of the viewer."""
        # pylint(access-member-before-definition)
        if mode == "settings":
            if self.dialog["settings"] is None:
                dialog = SettingsDialog(parent=self.parent, title="Settings", scale_factor=self.scale_factor)
                dialog.Ok.clicked.connect(lambda: self.accepted(mode))
                dialog.Cancel.clicked.connect(lambda: self.rejected(mode))
                dialog.set_viewer(self.viewer)
                self.dialog[mode] = dialog
                # self.default_settings = self.dialog[mode].get_settings()

            self.settings = self.dialog[mode].get_settings()
            self.dialog[mode].open()
            return

        if mode == "volume_render_settings":
            if self.dialog["volume_render_settings"] is None:
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

    def save_render(self):
        """Save the render to a file."""
        if self.dialog.get("settings") is None:
            self.viewer.saveRender("render")
        else:
            self.viewer.saveRender(self.dialog.get("settings").file_location)

    def save_dialog_settings(self):
        pass

    def apply_dialog_settings(self, mode, settings):
        pass
