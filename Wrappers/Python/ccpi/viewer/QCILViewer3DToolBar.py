from qtpy import QtWidgets, QtCore

from ccpi.viewer.utils.settings_tooltips import TOOLTIPS_3D_TOOLBAR
from ccpi.viewer.ui.SettingsDialog import SettingsDialog
from ccpi.viewer.ui.VolumeRenderSettingsDialog import VolumeRenderSettingsDialog
from ccpi.viewer.ui.CaptureRenderDialog import CaptureRenderDialog


class QCILViewer3DToolBar(QtWidgets.QToolBar):
    """
    A custom QToolBar embedded in a CILViewer window. The toolbar features
    drop-down QMenu widgets that contain QActions - users can interact with
    these to access various tools and dialogs that control the appearance 
    of the window contents.
    """

    def __init__(self, parent=None, viewer=None):
        """
        Creates the QCILViewer3DToolbar and sets up the associated QMenus and
        QActions. Checks whether any data has been loaded and is present in
        the provided viewer instance.

        viewer: The CILViewer instance that the toolbar will be embedded in.
        """
        if viewer is None:
            raise ValueError("A CILViewer instance must be provided to the QCILViewer3DToolBar.")
        self.viewer = viewer

        if self.viewer.img3D is None:
            self.data = None
        else:
            self.data = viewer.img3D

        super(QCILViewer3DToolBar, self).__init__(parent=parent)
        self.dialog = {"settings_2d": None, "settings_3d": None, "settings_render": None}

        self._setUpSettingsMenu()
        self._setUpCameraMenu()

    def _setUpSettingsMenu(self):
        """
        Configures the 3D Viewer settings drop-down QMenu. 
        The QMenu is populated with QActions that, when clicked, will
        open a corresponding settings dialog.

        The Slice Settings QAction opens a dialog controlling the viewer's 2D slice.
        The Volume Render Settings QAction opens a dialog controlling the viewer's 3D volume.
        """
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
        """
        Configures the Camera settings drop-down QMenu.

        The Reset Camera QAction resets the viewer's camera position.
        The Capture Render QAction opens a dialog for saving screenshots.
        """
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
        """
        Creates/opens a dialog. Dialogs are stored in a dictionary, allowing their
        settings to be loaded if they have been saved. 
        
        The method also checks whether new data has been loaded into the toolbar's viewer instance.
        If so, it will create new instances of the Settings and VolumeRenderSettings dialogs,
        with updated settings values retrieved from the image data. 
    
        mode: The key for the type of settings dialog that will be opened.
        """
        if self._isNewData(self.viewer.img3D):
            self._createSettingsDialog()
            self._createVolumeRenderSettingsDialog()

        if mode == "settings_2d":
            if self.dialog["settings_2d"] is None:
                self._createSettingsDialog()
            if self.viewer.img3D is not None:
                self.dialog[mode].getWidget("slice_visibility").setChecked(self.viewer.getSliceActorVisibility())
                self.dialog[mode].saveAllWidgetStates()
                self.dialog[mode].updateEnabledWidgetsWithSliceVisibility()
            self.dialog[mode].open()
            return

        if mode == "settings_3d":
            if self.dialog["settings_3d"] is None:
                self._createVolumeRenderSettingsDialog()
            volume_visibility = False
            if self.viewer.volume is not None:
                volume_visibility = self.viewer.getVolumeRenderVisibility()
            self.dialog[mode].getWidget("volume_visibility").setChecked(
                volume_visibility)
            self.dialog[mode].saveAllWidgetStates()
            self.dialog[mode].updateEnabledWidgetsWithVolumeVisibility()
            self.dialog[mode].open()
            return

        if mode == "settings_render":
            if self.dialog["settings_render"] is None:
                self._createCaptureRenderDialog()
            self.dialog[mode].open()
            return

    def _createSettingsDialog(self):
        mode = "settings_2d"
        dialog = SettingsDialog(parent=self.parent(), viewer=self.viewer, title="Slice Settings")
        self.dialog[mode] = dialog

    def _createVolumeRenderSettingsDialog(self):
        mode = "settings_3d"
        dialog = VolumeRenderSettingsDialog(parent=self.parent(), viewer=self.viewer, title="Volume Render Settings")
        self.dialog[mode] = dialog

    def _createCaptureRenderDialog(self):
        mode = "settings_render"
        dialog = CaptureRenderDialog(parent=self.parent(), viewer=self.viewer, title="Capture Render")
        self.dialog[mode] = dialog

    def _isNewData(self, data):
        """
        Checks whether new data has been loaded into the viewer instance, by
        comparing the toolbar's current data with the previously saved data.

        data: The data that will be checked.
        """
        if data != self.data:
            del self.data
            self.data = data
            return True
        else:
            return False

    def resetCamera(self):
        """
        Resets the 3D viewer's camera to the default camera position.
        """
        self.viewer.resetCameraToDefault()

        if self.viewer.img3D is None:
            return
        else:
            self.viewer.updatePipeline()