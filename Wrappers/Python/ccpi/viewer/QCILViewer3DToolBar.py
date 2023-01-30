from PySide2 import QtCore, QtWidgets
from ccpi.viewer.QCILRenderWindowInteractor import QCILRenderWindowInteractor
from ccpi.viewer import viewer2D, viewer3D, SLICE_ORIENTATION_YZ
from eqt.ui import FormDialog
from ccpi.viewer.ui.SettingsDialog import DialogSettings, DialogVolumeRenderSettings


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
        super(QCILViewer3DToolBar, self).__init__(parent=parent, **kwargs)
        self.dialog = {"2D": None, "3D": None}

        # 2D settings button
        settings_2d = QtWidgets.QToolButton()
        settings_2d.setText("Settings ⚙️")
        self.addWidget(settings_2d)
        settings_2d.clicked.connect(lambda: self.open_dialog("2D"))

        # 3D settings button
        settings_3d = QtWidgets.QToolButton()
        settings_3d.setText("Volume Render Settings ⚙️")
        self.addWidget(settings_3d)
        settings_3d.clicked.connect(lambda: self.open_dialog("3D"))

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
        print("Reset camera")
        self.viewer.resetCameraToDefault()
        self.viewer.updatePipeline()

    def change_orientation(self, dialog):
        """Change orientation of the viewer."""
        orientation = 1
        self.viewer.style.SetSliceOrientation(orientation)
        self.viewer.updatePipeline()

    def open_dialog(self, mode):
        # pylint(access-member-before-definition)
        if mode == "2D":
            # if not hasattr(self, "dialog"):
            if self.dialog["2D"] is None:
                dialog = DialogSettings(parent=self.parent, title="Settings")
                dialog.Ok.clicked.connect(lambda: self.accepted(mode))
                dialog.Cancel.clicked.connect(lambda: self.rejected(mode))
                dialog.set_viewer(self.viewer)
                self.dialog[mode] = dialog

            self.settings = self.dialog[mode].get_settings()
            # TODO: uppdate settings call
            self.dialog[mode].open()
            return

        if mode == "3D":
            if self.dialog["3D"] is None:
                dialog = DialogVolumeRenderSettings(parent=self.parent, title="Volume Render Settings")
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
        # TODO: open file browser for where to save
        # file save location in settings dialog
        # sQtWidgets.QFileDialog
        self.viewer.saveRender("hello.png")

    def save_dialog_settings(self):
        pass

    def apply_dialog_settings(self, mode, settings):
        pass
