import os
import sys
from functools import partial
from pathlib import Path

import ccpi.viewer.viewerLinker as vlink
import vtk
from ccpi.viewer import CILViewer2D, CILViewer
from ccpi.viewer.CILViewer2D import CILViewer2D
from ccpi.viewer.CILViewer import CILViewer
from ccpi.viewer.QCILViewerWidget import QCILDockableWidget
from ccpi.viewer.ui.dialogs import HDF5InputDialog, RawInputDialog, ViewerSettingsDialog
from ccpi.viewer.ui.qt_widgets import ViewerCoordsDockWidget
from ccpi.viewer.utils import cilPlaneClipper
from ccpi.viewer.utils.io import ImageReader
from eqt.threading import Worker
from eqt.ui.SessionDialogs import ErrorDialog
from eqt.ui.MainWindowWithSessionManagement import MainWindowWithProgressDialogs, MainWindowWithSessionManagement
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication, QFileDialog, QMainWindow, QSizePolicy


class ViewerMainWindow(MainWindowWithProgressDialogs):
    ''' Creates a window which is designed to house one or more viewers.
    Note: does not create a viewer as we don't know whether the user would like it to exist in a
    dockwidget or central widget
    Instead it creates a main window with many of the tools needed for a window
    that will house a viewer. 
    
    Methods of Interest
    -------------------
    self.createViewerCoordsDockWidget
        Creates a dock widget that displays the shape of the loaded image
        and if downsampled, the shape of the downsampled image. Allows user
        to select whether the coordinates on the viewer are shown in the
        original or downsampled image system.
    
    Assumes that at least one viewer is present, saved in self.viewers

    Parameters
    ----------
    title : str, optional
        The title of the window. The default is "ViewerMainWindow".
    app_name : str, optional
        The name of the application. The default is "ViewerMainWindow".
    settings_name : str, optional
        The name of the settings file. The default is None.
        If None, this is set to the app name.
    organisation_name : str, optional
        The name of the organisation. The default is None.
        If None, this is set to the app name.
    '''

    def __init__(self,
                 title="ViewerMainWindow",
                 app_name="ViewerMainWindow",
                 settings_name=None,
                 organisation_name=None):

        super(ViewerMainWindow, self).__init__(title,
                                               app_name,
                                               settings_name=settings_name,
                                               organisation_name=organisation_name)

        self.default_downsampled_size = 512**3

        self._viewers = []
        self._viewer_docks = []
        self._frames = []
        self._vs_dialog = None

        self.createViewerCoordsDockWidget()

    @property
    def viewers(self):
        '''The list of viewers in the window'''
        return self._viewers

    @property
    def viewer_docks(self):
        '''The list of dock widgets that contain the viewers'''
        return self._viewer_docks

    @property
    def frames(self):
        '''The list of frames in the window'''
        return self._frames

    @property
    def vs_dialog(self):
        '''The viewer settings dialog'''
        return self._vs_dialog

    @vs_dialog.setter
    def vs_dialog(self, value):
        self._vs_dialog = value

    def createAppSettingsDialog(self):
        '''Create a dialog to change the application settings, or open an existing one.
        This is a method in the MainWindowWithSessionManagement class, which we
        override here to make our own settings dialog'''
        if self.vs_dialog is None:
            self.vs_dialog = ViewerSettingsDialog(self)
            self.vs_dialog.Ok.clicked.connect(lambda: self.onAppSettingsDialogAccepted(self.vs_dialog))
            self.vs_dialog.Ok.clicked.connect(self.acceptViewerSettings)
            self.vs_dialog.Cancel.clicked.connect(self.vs_dialog.close)
        self.setAppSettingsDialogWidgets(self.vs_dialog)
        self.setViewerSettingsDialogWidgets()
        self.vs_dialog.open()

    def setViewerSettingsDialogWidgets(self):
        '''Set the viewer-specific widgets on the app settings dialog, based on the 
        current settings of the app.
        '''
        sw = self.vs_dialog.widgets

        if self.settings.value("vis_size") is not None:
            sw['vis_size_field'].setValue(float(self.settings.value("vis_size")))
        else:
            sw['vis_size_field'].setValue(self.getDefaultDownsampledSize() / (1024**3))

        if self.settings.value("use_gpu_volume_mapper") is not None:
            use_gpu = str(self.settings.value("use_gpu_volume_mapper"))
            sw['gpu_checkbox_field'].setChecked(use_gpu == "true")
        else:
            sw['gpu_checkbox_field'].setChecked(True)

    def acceptViewerSettings(self):
        '''This is called when the user clicks the OK button on the
        app settings dialog.
        Saves the viewer settings to the QSettings object.
        '''

        self.settings.setValue("vis_size", float(self.vs_dialog.widgets['vis_size_field'].value()))

        # Check if the user has changed the volume mapper setting:
        current_setting = self.settings.value("use_gpu_volume_mapper")

        if current_setting == str(self.vs_dialog.widgets['gpu_checkbox_field'].isChecked()):
            return
        else:
            bool_to_volume_mapper = {True: vtk.vtkSmartVolumeMapper(), False: vtk.vtkFixedPointVolumeRayCastMapper()}

            use_gpu_volume_mapper = self.vs_dialog.widgets['gpu_checkbox_field'].isChecked()

            self.settings.setValue("use_gpu_volume_mapper", use_gpu_volume_mapper)

            for viewer in self.viewers:
                if isinstance(viewer, CILViewer):
                    viewer.setVolumeMapper(bool_to_volume_mapper[use_gpu_volume_mapper])
                    if viewer.volume_render_initialised:
                        viewer.installVolumeRenderActorPipeline()
                        viewer.updatePipeline()

    def selectImage(self, label=None):
        ''' This selects opens a file dialog for the user to select the image
        and gets the user to enter relevant data, but does not load them on a viewer yet.
        
        Parameters
        ----------
        label : QLabel, optional
            The label to display the basename of the file name on.
        
        Returns
        -------
        file : str
            The file name of the image selected by the user.
        '''
        dialog = QFileDialog()
        files = list(dialog.getOpenFileNames(self, "Select Images")[0])
        self.raw_attrs = {}
        self.hdf5_attrs = {}
        if files is None:
            return
        if len(files) == 1:
            file = files[0]
            file_extension = Path(file).suffix.lower()
            if 'raw' in file_extension:
                raw_dialog = RawInputDialog(self, file)
                raw_dialog.Ok.clicked.connect(lambda: self.getRawAttrsFromDialog(raw_dialog))
                # See https://doc.qt.io/qt-6/qdialog.html#exec
                # Shows a modal dialog, blocking until the user closes it.
                raw_dialog.exec()
                if self.raw_attrs == {}:
                    return None
            elif file_extension in ['.nxs', '.h5', '.hdf5']:
                dialog = HDF5InputDialog(self, file)
                dialog.Ok.clicked.connect(lambda: self.getHDF5AttrsFromDialog(dialog))
                # See https://doc.qt.io/qt-6/qdialog.html#exec
                # Shows a modal dialog, blocking until the user closes it.
                dialog.exec()
                if self.hdf5_attrs == {}:
                    return None
            self.input_dataset_file = file
        else:
            self.input_dataset_file = files

        if label is not None:
            label.setText(os.path.basename(files[0]))

        return self.input_dataset_file

    def getRawAttrsFromDialog(self, dialog):
        '''Gets the raw attributes from the dialog and saves them to the
        raw_attrs attribute of the window.
        Also closes the dialog.
        
        Parameters
        ----------
        dialog : RawInputDialog
            The dialog to get the attributes from.
        '''
        self.raw_attrs = dialog.getRawAttrs()
        dialog.close()

    def getHDF5AttrsFromDialog(self, dialog):
        '''
        Gets the HDF5 attributes from the dialog and saves them to the
        hdf5_attrs attribute of the window.
        Also closes the dialog.
        
        Parameters
        ----------
        dialog : HDF5InputDialog
            The dialog to get the attributes from.
        '''

        self.hdf5_attrs = dialog.getHDF5Attributes()
        dialog.close()

    def createViewerCoordsDockWidget(self):
        '''
        Creates a dock widget which contains widgets for displaying the 
        image shown on the viewer, and the coordinate system of the viewer.
        '''
        dock = ViewerCoordsDockWidget(self)
        self.viewer_coords_dock = dock
        self.viewer_coords_dock.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        dock.getWidgets()['coords_combo_field'].currentIndexChanged.connect(self.updateViewerCoords)

    def placeViewerCoordsDockWidget(self):
        '''
        Places the viewer coords dock widget in the main window.
        May be overridden by subclasses to place the dock widget in a different
        location.
        This method is a courtesy method and gets never explicitly called.
        So it's the user's responsibility to place the widget, for example by
        calling this method.
        '''
        self.addDockWidget(Qt.BottomDockWidgetArea, self.viewer_coords_dock)

    def setViewersInputFromDialog(self, viewers, input_num=1):
        '''Displays an image in the viewer(s).'''
        image_file = self.selectImage()
        if image_file is not None:
            self.setViewersInput(image_file, viewers, input_num=input_num)

    def setViewersInput(self, image, viewers, input_num=1, image_name=None):
        '''
        Displays an image in the viewer/s.

        Parameters
        ----------
        viewer: CILViewer2D or CILViewer, or list of CILViewer2D or CILViewer
            The viewer(s) to display the image in.
        image: str, list or vtk.vtkImageData
            The image or images to display. If a string, it is assumed to be a file name.
        input_num : int
            The input number to the viewer. 1 or 2, where 1 is the default image and 2 is the overlay
            image. Only used if the viewer is a 2D viewer.
        image_name : str
            The name of the image. If not given, the file name is used.
            Must be set if no file name is given.
        '''
        raw_image_attrs = self.raw_attrs
        hdf5_image_attrs = self.hdf5_attrs
        dataset_name = hdf5_image_attrs.get('dataset_name')
        resample_z = hdf5_image_attrs.get('resample_z')
        target_size = self.getTargetImageSize()
        if isinstance(image, str) or isinstance(image, list):
            image_reader = ImageReader(file_name=image)
        else:
            image_reader = ImageReader(vtk_image=image)
        image_reader.SetTargetSize(target_size)
        image_reader.SetRawImageAttributes(raw_image_attrs)
        image_reader.SetHDF5DatasetName(dataset_name)
        image_reader.SetResampleZ(resample_z)
        image_reader_worker = Worker(image_reader.Read)
        self.createUnknownProgressWindow("Reading Image")
        if image_name is None and isinstance(image, str):
            image_name = image
        image_reader_worker.signals.result.connect(
            partial(self.displayImage, viewers, input_num, image_reader, image_name))
        image_reader_worker.signals.finished.connect(lambda: self.finishProcess("Reading Image"))
        image_reader_worker.signals.error.connect(self.processErrorDialog)
        self.threadpool.start(image_reader_worker)

    def processErrorDialog(self, error, **kwargs):
        '''
        Creates an error dialog to display the error.
        '''
        dialog = ErrorDialog(self, "Error", str(error[1]), str(error[2]))
        dialog.open()

    def displayImage(self, viewers, input_num, reader, image_name, image):
        '''
        Displays an image on the viewer/s.

        Parameters
        ----------
        viewers: CILViewer2D or CILViewer, or list of CILViewer2D or CILViewer
            The viewer(s) to display the image on.
        input_num : int
            The input number to the viewer. 1 or 2. Only used if the viewer is
            a 2D viewer. 1 is the default image and 2 is the overlay image.
        reader: ImageReader
            The reader used to read the image. This contains some extra info about the
            original image file.
        image_name: str
            The image file name, or label to display on the viewer.
        image: vtkImageData
            The image to display.

        '''
        if image is None:
            return
        if not isinstance(viewers, list):
            viewers = [viewers]
        for viewer in viewers:
            if input_num == 1:
                viewer.setInputData(image)
            elif input_num == 2:
                if isinstance(viewer, CILViewer2D):
                    viewer.setInputData2(image)
                # If input_num=2 we don't want to update the viewer coords dock widget
                # with the name of the image file, as this is the overlay image.
                image_name = None
        self.updateGUIForNewImage(reader, viewer, image_name)

    def updateGUIForNewImage(self, reader=None, viewer=None, image_name=None):
        '''
        Updates the GUI for a new image:
        - Updates the viewer coordinates dock widget with the displayed image dimensions
            and the loaded image dimensions (if a reader is provided)
        - Updates the viewer coordinates dock widget with the image file name
        In subclass, may want to add more functionality.
        '''
        self.updateViewerCoordsDockWidgetWithCoords(reader)
        self.updateViewerCoordsDockWidgetWithImageFileName(image_name)

    def updateViewerCoordsDockWidgetWithImageFileName(self, image_name=None):
        '''
        Updates the viewer coordinates dock widget with the image file name.

        Parameters
        ----------
        image_file: str
            The image file name.
        '''
        if image_name is None:
            return

        widgets = self.viewer_coords_dock.getWidgets()
        widgets['image_field'].clear()
        widgets['image_field'].addItem(image_name)
        widgets['image_field'].setCurrentIndex(0)

    def updateViewerCoordsDockWidgetWithCoords(self, reader=None):
        '''
        Updates the viewer coordinates dock widget with the displayed image dimensions
        and the loaded image dimensions (if a reader is provided)
        
        Parameters
        ----------
        reader: ImageReader
            The reader used to read the image. This contains some extra info about the
            original image file.
        '''

        viewer = self.viewer_coords_dock.viewers[0]

        if not isinstance(viewer, (CILViewer2D, CILViewer)):
            return

        image = viewer.img3D

        if image is None:
            return

        widgets = self.viewer_coords_dock.getWidgets()

        # Update the coordinates: ------------------------------

        displayed_image_dims = str(list(image.GetDimensions()))

        widgets['coords_combo_field'].setCurrentIndex(0)

        widgets['loaded_image_dims_field'].setVisible(True)
        widgets['loaded_image_dims_label'].setVisible(True)

        if reader is None:
            # If reader is None, then we have no info about the original
            # image file, or whether it was resampled.
            resampled = False
        else:
            loaded_image_attrs = reader.GetLoadedImageAttrs()
            resampled = loaded_image_attrs.get('resampled')

            if resampled:
                # Check if the image was actually resampled:
                original_image_attrs = reader.GetOriginalImageAttrs()
                original_image_dims = original_image_attrs.get('shape')
                if list(original_image_dims) == list(displayed_image_dims):
                    resampled = False

        widgets['coords_warning_field'].setVisible(resampled)
        widgets['coords_info_field'].setVisible(resampled)
        widgets['coords_combo_field'].setEnabled(resampled)
        widgets['displayed_image_dims_field'].setVisible(resampled)
        widgets['displayed_image_dims_label'].setVisible(resampled)

        if not resampled:
            widgets['loaded_image_dims_field'].setText(displayed_image_dims)
        else:
            original_image_attrs = reader.GetOriginalImageAttrs()
            original_image_dims = str(list(original_image_attrs.get('shape')))
            spacing = image.GetSpacing()
            for _viewer in self.viewer_coords_dock.viewers:
                _viewer.setVisualisationDownsampling(spacing)

            widgets['loaded_image_dims_field'].setText(original_image_dims)
            widgets['displayed_image_dims_field'].setText(displayed_image_dims)

    def updateViewerCoords(self):
        '''
        Updates the coordinate system of the viewer/s associated with the 
        ViewerCoordinatesDockWidget and the displayed image
        dimensions, for the image on that viewer.

        '''
        viewer_coords_widgets = self.viewer_coords_dock.getWidgets()
        viewer = self.viewer_coords_dock.viewers[0]
        shown_resample_rate = viewer.getVisualisationDownsampling()
        for viewer in self.viewer_coords_dock.viewers:
            if isinstance(viewer, CILViewer2D) and viewer.img3D is not None:
                if viewer_coords_widgets['coords_combo_field'].currentIndex() == 0:
                    viewer.setDisplayUnsampledCoordinates(True)
                    if shown_resample_rate != [1, 1, 1]:
                        viewer_coords_widgets['coords_warning_field'].setVisible(True)
                    else:
                        viewer_coords_widgets['coords_warning_field'].setVisible(False)
                else:
                    viewer.setDisplayUnsampledCoordinates(False)
                    viewer_coords_widgets['coords_warning_field'].setVisible(False)

                viewer.updatePipeline()

    def getTargetImageSize(self):
        ''' Get the target size for an image to be displayed in bytes.'''
        if self.settings.value("vis_size") is not None:
            target_size = float(self.settings.value("vis_size")) * (1024**3)
        else:
            target_size = self.getDefaultDownsampledSize()
        return target_size

    def setDefaultDownsampledSize(self, value):
        ''' Set the default size for an image to be displayed in bytes'''
        self.default_downsampled_size = int(value)

    def getDefaultDownsampledSize(self):
        ''' Get the default size for an image to be displayed in bytes'''
        return self.default_downsampled_size


class ViewerMainWindowWithSessionManagement(MainWindowWithSessionManagement, ViewerMainWindow):
    ''' Creates a window which is designed to house one or more viewers.
    Note: does not create a viewer as we don't know whether the user would like it to exist in a
    dockwidget or central widget
    Instead it creates a main window with many of the tools needed for a window
    that will house a viewer.

    Parameters
    ----------
    title : str, optional
        The title of the window. The default is "ViewerMainWindowWithSessionManagement".
    app_name : str, optional
        The name of the application. The default is "ViewerMainWindowWithSessionManagement".
    settings_name : str, optional
        The name of the settings file. The default is None.
        If None, this is set to the app name.
    organisation_name : str, optional
        The name of the organisation. The default is None.
        If None, this is set to the app name.
    '''

    def __init__(self,
                 title="ViewerMainWindowWithSessionManagement",
                 app_name="ViewerMainWindowWithSessionManagement",
                 settings_name=None,
                 organisation_name=None):

        super(ViewerMainWindowWithSessionManagement, self).__init__(title,
                                                                    app_name,
                                                                    settings_name=settings_name,
                                                                    organisation_name=organisation_name)


class TwoViewersMainWindowMixin(object):
    '''
    Provides a mixin for a TwoViewersMainWindow or a TwoViewersMainWindowWithSessionManagement class.
    Provides the setupTwoViewers method, which:
    creates a window containing two viewers, both in dockwidgets.
    The viewers are linked together, so that they share the same
    camera position and orientation.

    Also provides other methods for adding viewers, and for
    setting up the viewer coordinates dockwidget.
    
    If a viewer is 2D, then a :code:`cilPlaneClipper` will be added to the viewer
    to clip any 3D object in the view, such as a sphere source.
    
    Properties of note:
        viewers: a list of the two viewers
        frames: a list of the two frames
        viewer_docks: a list of the two viewer docks


    '''

    def setupTwoViewers(self, viewer1_type, viewer2_type=None):
        '''
        Adds the viewers as dockwidgets inside the central widget.
        Also adds a ViewerCoordinatesDockWidget to the window.

        Parameters
        ----------
        viewer1_type: '2D' or '3D'
            The type of the first viewer.
            If '2D', then a CILViewer2D is created.
            If '3D', then a CILViewer is created.
        viewer2_type: '2D' or '3D', or None, optional
            The type of the second viewer.
            If '2D', then a CILViewer2D is created.
            If '3D', then a CILViewer is created.
            If None, then no second viewer is created.
        '''
        if not hasattr(self, 'central_widget'):
            cw = QMainWindow()
            cw.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.setCentralWidget(cw)
            self.central_widget = cw

        self.addViewer(viewer1_type)

        if viewer2_type is not None:
            self.addViewer(viewer2_type)

        self.placeViewerCoordsDockWidget()

        self.viewer_coords_dock.viewers = self.viewers

        self.setupPlaneClipping()

    def addViewer(self, viewer_type):
        '''
        Add a viewer to the window, inside a DockWidget, within the
        central widget.

        Saves the viewer to self.viewers, saves the frame to self.frames,
        and saves the dock to self.viewer_docks.

        If any viewers are already present, the new viewer will be added
        to the right of the window.
        
        Parameters
        ----------
        viewer_type: '2D' or '3D'
            The type of viewer to add to the window.
        '''
        if len(self.viewers) == 2:
            raise ValueError("Cannot add more than two viewers to this window.")

        if viewer_type == '2D':
            interactor_style = vlink.Linked2DInteractorStyle
            dock_title = "2D View"
            viewer = CILViewer2D
        elif viewer_type == '3D':
            interactor_style = vlink.Linked3DInteractorStyle
            dock_title = "3D View"
            viewer = CILViewer
        else:
            raise ValueError("viewer_type must be either '2D' or '3D'")

        dock = QCILDockableWidget(viewer=viewer, shape=(600, 600), interactorStyle=interactor_style, title=dock_title)
        dock.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        if len(self.viewers) == 0:
            self.central_widget.addDockWidget(Qt.LeftDockWidgetArea, dock)
        elif len(self.viewers) == 1:
            self.central_widget.addDockWidget(Qt.RightDockWidgetArea, dock)
            self.linkedViewersSetUp([self.viewers[0], dock.frame.viewer])
            self.linker.enable()

        self.viewers.append(dock.frame.viewer)
        self.frames.append(dock.frame)
        self.viewer_docks.append(dock)

    def linkedViewersSetUp(self, viewers):
        '''
        Link two viewers together.
        
        Parameters
        ----------
        viewers : list of CILViewer or CILViewer2D
            The viewers to link together.
        '''
        v1 = viewers[0]
        v2 = viewers[1]
        self.linker = vlink.ViewerLinker(v1, v2)
        self.linker.setLinkPan(False)
        self.linker.setLinkZoom(False)
        self.linker.setLinkWindowLevel(True)
        self.linker.setLinkSlice(True)

    def showHideViewer(self, viewer_num, show=True):
        '''Show or  hide a viewer.
        
        Parameters
        ----------
        viewer_num : int
            The index of the viewer to show or hide, in the list self.viewers.
        show : bool, optional
            Whether to show the viewer. Default is True.
        '''
        if not show:
            self.viewer_docks[viewer_num].hide()
        else:
            self.viewer_docks[viewer_num].show()

    def setupPlaneClipping(self):
        '''
        Set up plane clipping for all 2D viewers.
        '''
        for viewer in self.viewers:
            if isinstance(viewer, CILViewer2D):
                viewer.PlaneClipper = cilPlaneClipper()
                viewer.PlaneClipper.SetInteractorStyle(viewer.style)
                viewer.style.AddObserver("MouseWheelForwardEvent", viewer.PlaneClipper.UpdateClippingPlanes, 0.9)
                viewer.style.AddObserver("MouseWheelBackwardEvent", viewer.PlaneClipper.UpdateClippingPlanes, 0.9)
                viewer.style.AddObserver("KeyPressEvent", viewer.PlaneClipper.UpdateClippingPlanes, 0.9)

    def placeViewerCoordsDockWidget(self):
        '''
        Positions the viewer coords dock widget below the viewers
        '''
        self.addDockWidget(Qt.BottomDockWidgetArea, self.viewer_coords_dock)


class TwoViewersMainWindow(TwoViewersMainWindowMixin, ViewerMainWindow):
    '''
    Creates a window containing two viewers, both in dockwidgets.
    The viewers are linked together, so that they share the same
    camera position and orientation.
    
    If a viewer is 2D, then a :code:`cilPlaneClipper` will be added to the
    viewer to clip any 3D object in the view, such as a sphere source.
    
    Properties of note:
        viewers: a list of the two viewers
        frames: a list of the two frames
        viewer_docks: a list of the two viewer docks
    
    Parameters
    ----------
    title : str, optional
        The title of the window. The default is "TwoViewersMainWindow".
    app_name : str, optional
        The name of the application. The default is "TwoViewersMainWindow".
    settings_name : str, optional
        The name of the settings file. The default is None.
        If None, this is set to the `app_name`.
    organisation_name : str, optional
        The name of the organisation. The default is None.
        If None, this is set to the `app_name`.
    viewer1_type: '2D' or '3D', default '2D'
        The type of the first viewer. 
        If '2D', then a CILViewer2D is created.
        If '3D', then a CILViewer is created.
    viewer2_type: '2D' or '3D', or None, optional. Default '3D'
        The type of the second viewer. 
        If '2D', then a CILViewer2D is created.
        If '3D', then a CILViewer is created.
        If None, then no second viewer is created.
    '''

    def __init__(self,
                 title="TwoViewersMainWindow",
                 app_name="TwoViewersMainWindow",
                 settings_name=None,
                 organisation_name=None,
                 viewer1_type='2D',
                 viewer2_type='3D'):

        super(TwoViewersMainWindow, self).__init__(title, app_name, settings_name, organisation_name)
        self.setupTwoViewers(viewer1_type, viewer2_type)


class TwoViewersMainWindowWithSessionManagement(TwoViewersMainWindowMixin, ViewerMainWindowWithSessionManagement):
    '''
    Creates a window containing two viewers, both in dockwidgets.
    This main window has methods for saving and loading sessions.

    The viewers are linked together, so that they share the same
    camera position and orientation.
    
    If a viewer is 2D, then a :code:`cilPlaneClipper` will be added to the
    viewer to clip any 3D object in the view, such as a sphere source.
    
    Properties of note:
        viewers: a list of the two viewers
        frames: a list of the two frames
        viewer_docks: a list of the two viewer docks

    This class is meant to be subclassed, and the subclass should implement the following methods:
     - getSessionConfig
     - finishLoadConfig
     as these deal with the session saving and loading. See 'MainWindowWithSessionManagement' for more details.

    
    Parameters
    ----------
    title : str, optional
        The title of the window.
        The default is "TwoViewersMainWindowWithSessionManagement".
    app_name : str, optional
        The name of the application.
        The default is "TwoViewersMainWindowWithSessionManagement".
    settings_name : str, optional
        The name of the settings file. The default is None.
        If None, this is set to the app name.
    organisation_name : str, optional
        The name of the organisation. The default is None.
        If None, this is set to the app name.
    viewer1_type: '2D' or '3D', default '2D'
        The type of the first viewer. 
        If '2D', then a CILViewer2D is created.
        If '3D', then a CILViewer is created.
    viewer2_type: '2D' or '3D', or None, optional. Default '3D'
        The type of the second viewer. 
        If '2D', then a CILViewer2D is created.
        If '3D', then a CILViewer is created.
        If None, then no second viewer is created.
    '''

    def __init__(self,
                 title="TwoViewersMainWindowWithSessionManagement",
                 app_name="TwoViewersMainWindowWithSessionManagement",
                 settings_name=None,
                 organisation_name=None,
                 viewer1_type='2D',
                 viewer2_type='3D'):
        super(TwoViewersMainWindowWithSessionManagement, self).__init__(title, app_name, settings_name,
                                                                        organisation_name)
        self.setupTwoViewers(viewer1_type, viewer2_type)


# For running example window -----------------------------------------------------------


def create_main_window():
    window = TwoViewersMainWindow("Test Viewer Main Window", 'Test Viewer Main Window')
    return window


def main():
    app = QApplication(sys.argv)
    window = create_main_window()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
