
import os
import sys
from functools import partial
from pathlib import Path

import ccpi.viewer.viewerLinker as vlink
import vtk
from ccpi.viewer import viewer2D, viewer3D
from ccpi.viewer.CILViewer2D import CILViewer2D
from ccpi.viewer.QCILViewerWidget import QCILDockableWidget
from ccpi.viewer.ui.dialogs import (HDF5InputDialog, RawInputDialog,
                                    ViewerSessionSettingsDialog,
                                    ViewerSettingsDialog)
from ccpi.viewer.ui.qt_widgets import ViewerCoordsDockWidget
from ccpi.viewer.utils import cilPlaneClipper
from ccpi.viewer.utils.io import ImageReader
from eqt.threading import Worker
from eqt.ui.SessionDialogs import ErrorDialog
from eqt.ui.SessionMainWindow import ProgressMainWindow, SessionMainWindow
from PySide2 import QtCore
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication, QCheckBox, QFileDialog, QMainWindow


class ViewerMainWindow(ProgressMainWindow):
    ''' Creates a window which is designed to house one or more viewers.
    Note: does not create a viewer as we don't know whether the user would like it to exist in a
    dockwidget or central widget
    Instead it creates a main window with many of the tools needed for a window
    that will house a viewer. 
    
    Assumes that at least one viewer is present, saved in self.viewers

    Parameters
    ----------
    title : str, optional
        The title of the window. The default is "ViewerMainWindow".
    app_name : str, optional
        The name of the application. The default is None.
    settings_name : str, optional
        The name of the settings file. The default is None.
    organisation_name : str, optional
        The name of the organisation. The default is None.
    '''

    def __init__(self,
                 title="ViewerMainWindow",
                 app_name=None,
                 settings_name=None,
                 organisation_name=None,
                 *args,
                 **kwargs):

        super(ViewerMainWindow, self).__init__(title,
                                               app_name,
                                               settings_name=settings_name,
                                               organisation_name=organisation_name)

        self.default_downsampled_size = 512**3

        self.createViewerCoordsDockWidget()
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.viewer_coords_dock)

        self.viewers = []

    def createAppSettingsDialog(self):
        '''Create a dialog to change the application settings.
        This is a method in the SessionMainWindow class, which we
        override here to make our own settings dialog'''
        dialog = ViewerSettingsDialog(self)
        dialog.Ok.clicked.connect(lambda: self.onAppSettingsDialogAccepted(dialog))
        dialog.Cancel.clicked.connect(dialog.close)
        self.setAppSettingsDialogWidgets(dialog)
        dialog.open()

    def setAppSettingsDialogWidgets(self, dialog):
        '''Set the widgets on the app settings dialog, based on the 
        current settings of the app.
        
        Parameters
        ----------
        dialog : ViewerSettingsDialog
            The dialog to set the widgets on.
        '''
        super().setAppSettingsDialogWidgets(dialog)
        sw = dialog.widgets

        if self.settings.value("vis_size") is not None:
            sw['vis_size_field'].setValue(float(self.settings.value("vis_size")))
        else:
            sw['vis_size_field'].setValue(self.getDefaultDownsampledSize() / (1024**3))

        if self.settings.value("volume_mapper") is not None:
            sw['gpu_checkbox_field'].setChecked(self.settings.value("volume_mapper") == "gpu")
        else:
            sw['gpu_checkbox_field'].setChecked(True)

    def onAppSettingsDialogAccepted(self, settings_dialog):
        '''This is called when the user clicks the OK button on the
        app settings dialog. We override this method to save the
        settings to the QSettings object.
        
        Parameters
        ----------
        settings_dialog : ViewerSettingsDialog
            The dialog to get the settings from.
        '''
        super().onAppSettingsDialogAccepted(settings_dialog)

        self.settings.setValue("vis_size", float(settings_dialog.widgets['vis_size_field'].value()))

        if settings_dialog.widgets['gpu_checkbox_field'].isChecked():
            self.settings.setValue("volume_mapper", "gpu")
            for viewer in self.viewers:
                if isinstance(viewer, viewer3D):
                    viewer.volume_mapper = vtk.vtkSmartVolumeMapper()
        else:
            self.settings.setValue("volume_mapper", "cpu")

    def selectImage(self, label=None):
        ''' This selects opens a file dialog for the user to select the image
        and gets the user to enter relevant data, but does not load them on a viewer yet.
        
        Parameters
        ----------
        label : QLabel, optional
            The label to display the basename of the file name on.
        '''
        dialog = QFileDialog()
        file = dialog.getOpenFileName(self, "Select Images")[0]
        file_extension = Path(file).suffix.lower()
        self.raw_attrs = {}
        self.hdf5_attrs = {}
        if 'tif' in file_extension:
            print('tif ', file)
            file = os.path.dirname(file)
        if 'raw' in file_extension:
            raw_dialog = RawInputDialog(self, file)
            raw_dialog.Ok.clicked.connect(lambda: self.getRawAttrsFromDialog(raw_dialog))
            raw_dialog.exec_()
        elif file_extension in ['.nxs', '.h5', '.hdf5']:
            raw_dialog = HDF5InputDialog(self, file)
            raw_dialog.Ok.clicked.connect(lambda: self.getHDF5AttrsFromDialog(raw_dialog))
            raw_dialog.exec_()

        self.input_dataset_file = file
        if label is not None:
            label.setText(os.path.basename(file))

        return file, self.raw_attrs, self.hdf5_attrs

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
        dock.getWidgets()['coords_combo_field'].currentIndexChanged.connect(self.updateViewerCoords)

    def setViewersInput(self, viewers, input_num=1):
        '''
        Opens a file dialog to select an image file and then displays it in the viewer.

        Parameters
        ----------
        viewer: CILViewer2D or CILViewer, or list of CILViewer2D or CILViewer
            The viewer(s) to display the image in.
        input_num : int
            The input number to the viewer. 1 or 2. Only used if the viewer is
            a 2D viewer. 1 is the default image and 2 is the overlay image.
        '''
        image_file, raw_image_attrs, hdf5_image_attrs = self.selectImage()

        dataset_name = hdf5_image_attrs.get('dataset_name')
        resample_z = hdf5_image_attrs.get('resample_z')
        print("The image attrs: ", raw_image_attrs)
        target_size = self.getTargetImageSize()
        image_reader = ImageReader(file_name=image_file,
                                   target_size=target_size,
                                   raw_image_attrs=raw_image_attrs,
                                   hdf5_dataset_name=dataset_name,
                                   resample_z=resample_z)
        image_reader_worker = Worker(image_reader.Read)
        self.threadpool.start(image_reader_worker)
        self.createUnknownProgressWindow("Reading Image")
        image_reader_worker.signals.result.connect(
            partial(self.displayImage, viewers, input_num, image_reader, image_file))
        image_reader_worker.signals.finished.connect(self.finishProcess("Reading Image"))
        image_reader_worker.signals.error.connect(self.processErrorDialog)

    def processErrorDialog(self, error, **kwargs):
        '''
        Creates an error dialog to display the error.
        '''
        dialog = ErrorDialog(self, "Error", str(error[1]), str(error[2]))
        dialog.open()

    def displayImage(self, viewers, input_num, reader, image_file, image):
        '''
        Displays an image on the viewer/s.

        Parameters
        ----------
        viewer: CILViewer2D or CILViewer, or list of CILViewer2D or CILViewer
            The viewer(s) to display the image on.
        input_num : int
            The input number to the viewer. 1 or 2. Only used if the viewer is
            a 2D viewer. 1 is the default image and 2 is the overlay image.
        reader: ImageReader
            The reader used to read the image. This contains some extra info about the
            original image file.
        image: vtkImageData
            The image to display.
        image_file: str
            The image file name.
        '''
        if image is None:
            return
        if not isinstance(viewers, list):
            viewers = [viewers]
        for viewer in viewers:
            if input_num == 1:
                viewer.setInputData(image)
                if viewer == self.viewers[0]:
                    self.updateViewerCoordsDockWidgetWithCoords(reader)
            elif input_num == 2:
                if isinstance(viewer, CILViewer2D):
                    viewer.setInputData2(image)
        self.updateGUIForNewImage(reader, viewer, image_file)

    def updateGUIForNewImage(self, reader=None, viewer=None, image_file=None):
        '''
        Updates the GUI for a new image:
        - Updates the viewer coordinates dock widget with the displayed image dimensions
            and the loaded image dimensions (if a reader is provided)
        - Updates the viewer coordinates dock widget with the image file name
        In subclass, may want to add more functionality.
        '''
        self.updateViewerCoordsDockWidgetWithCoords(reader)
        self.updateViewerCoordsDockWidgetWithImageFileName(image_file)

    def updateViewerCoordsDockWidgetWithImageFileName(self, image_file=None):
        '''
        Updates the viewer coordinates dock widget with the image file name.

        Parameters
        ----------
        image_file: str
            The image file name.
        '''
        if image_file is None:
            return

        widgets = self.viewer_coords_dock.getWidgets()
        widgets['image_field'].clear()
        widgets['image_field'].addItem(image_file)
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

        if not isinstance(viewer, (viewer2D, viewer3D)):
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
        viewer = viewer_coords_widgets.viewers[0]
        shown_resample_rate = viewer.getVisualisationDownsampling()
        for viewer in viewer_coords_widgets.viewers:
            if viewer.img3D is not None:
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



class ViewerSessionMainWindow(SessionMainWindow, ViewerMainWindow):
    ''' Creates a window which is designed to house one or more viewers.
    Note: does not create a viewer as we don't know whether the user would like it to exist in a
    dockwidget or central widget
    Instead it creates a main window with many of the tools needed for a window
    that will house a viewer.

    Parameters
    ----------
    title: str
        The title of the window
    app_name: str
        The name of the application
    settings_name: str
        The name of the settings file
    organisation_name: str
        The name of the organisation
    '''

    def __init__(self,
                 title="ViewerMainWindow",
                 app_name=None,
                 settings_name=None,
                 organisation_name=None,
                 *args,
                 **kwargs):


        ViewerMainWindow.__init__(self, title, app_name,
                                    settings_name=settings_name,
                                    organisation_name=organisation_name)
        
        self._setupSessionMainWindow()


    def createAppSettingsDialog(self):
        '''Create a dialog to change the application settings.
        This is a method in the SessionMainWindow class, which we
        override here to make our own settings dialog
        '''
        dialog = ViewerSessionSettingsDialog(self)
        dialog.Ok.clicked.connect(lambda: self.onAppSettingsDialogAccepted(dialog))
        dialog.Cancel.clicked.connect(dialog.close)
        self.setAppSettingsDialogWidgets(dialog)
        dialog.open()

    def setAppSettingsDialogWidgets(self, dialog):
        '''Set the widgets on the app settings dialog, based on the 
        current settings of the app
        
        Parameters
        ----------
        dialog : ViewerSessionSettingsDialog
            The settings dialog
        '''
        super().setAppSettingsDialogWidgets(dialog)
        sw = dialog.widgets
        if self.settings.value('copy_files') is not None:
            sw['copy_files_checkbox_field'].setChecked(int(self.settings.value('copy_files')))


    def onAppSettingsDialogAccepted(self, settings_dialog):
        '''This is called when the user clicks the OK button on the
        app settings dialog. We override this method to save the
        settings to the QSettings object.
        
        Parameters
        ----------
        settings_dialog : ViewerSessionSettingsDialog
            The settings dialog
        '''
        super().onAppSettingsDialogAccepted(settings_dialog)

        if settings_dialog.widgets['copy_files_checkbox_field'].isChecked():
            self.settings.setValue("copy_files", 1)
        else:
            self.settings.setValue("copy_files", 0)


class TwoViewersMainWindow(ViewerMainWindow):
    ''' Creates a window containing two viewers, both in dockwidgets.
    The viewers are linked together, so that they share the same
    camera position and orientation.
    
    If a viewer is 2D, then it will be PlaneClipped.
    
    Properties of note:
        viewers: a list of the two viewers
        frames: a list of the two frames
        viewer_docks: a list of the two viewer docks

    Parameters
    ----------
    title : str
        The title of the window
    app_name : str
        The name of the application
    settings_name : str
        The name of the settings file
    organisation_name : str
        The name of the organisation
    viewer1 : CILViewer2D or CILViewer
        The class of the first viewer
    viewer2 : CILViewer2D, CILViewer, or None, optional
        The class of the second viewer
    '''

    def __init__(self,
                 title="StandaloneViewer",
                 app_name="Standalone Viewer",
                 settings_name=None,
                 organisation_name=None,
                 viewer1=viewer2D,
                 viewer2=viewer3D):
        ViewerMainWindow.__init__(self, title, app_name, settings_name, organisation_name)

        cw = QMainWindow()
        self.setCentralWidget(cw)
        self.central_widget = cw

        self.frames = []
        self.viewer_docks = []

        self.addViewer(viewer1)

        if viewer2 is not None:
            self.addViewer(viewer2)

        self.viewer_coords_dock.setViewers(self.viewers)

        self.setupPlaneClipping()


    def addViewer(self, viewer):
        '''Add a viewer to the window, inside a DockWidget, within the
        central widget.

        Saves the viewer to self.viewers, saves the frame to self.frames,
        and saves the dock to self.viewer_docks.

        If any viewers are already present, the new viewer will be added
        to the right of the window.
        
        Parameters
        ----------
        viewer : CILViewer or CILViewer2D
            The viewer to add to the window.
        '''
        if len(self.viewers) == 2:
            raise ValueError("Cannot add more than two viewers to this window.")

        if viewer == viewer2D:
            interactor_style = vlink.Linked2DInteractorStyle
            dock_title = "2D View"
        elif viewer == viewer3D:
            interactor_style = vlink.Linked3DInteractorStyle
            dock_title = "3D View"
        else:
            raise ValueError("viewer must be either viewer2D or viewer3D")

        dock = QCILDockableWidget(viewer=viewer,
                                shape=(600, 600),
                                interactorStyle=interactor_style,
                                title=dock_title)
        
        if self.viewers == []:
            self.central_widget.addDockWidget(Qt.LeftDockWidgetArea, dock)
        else:
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
        self.linker.setLinkPan(True)
        self.linker.setLinkZoom(True)
        self.linker.setLinkWindowLevel(True)
        self.linker.setLinkSlice(True)

    def showHideViewer(self, viewer_num):
        '''Show or  hide a viewer, depending on its current state.
        
        Parameters
        ----------
        viewer_num : int
            The index of the viewer to show or hide, in the list self.viewers.
        '''
        if self.viewer_docks[viewer_num].isVisible():
            self.viewer_docks[viewer_num].hide()
        else:
            self.viewer_docks[viewer_num].show()


    def setupPlaneClipping(self):
        '''
        Set up plane clipping for all 2D viewers.
        '''
        for viewer in self.viewers:
            if isinstance(viewer, viewer2D):
                viewer.PlaneClipper = cilPlaneClipper()
                viewer.PlaneClipper.SetInteractorStyle(viewer.style)
                viewer.style.AddObserver(
                    "MouseWheelForwardEvent",
                    viewer.PlaneClipper.UpdateClippingPlanes, 0.9)
                viewer.style.AddObserver(
                    "MouseWheelBackwardEvent",
                    viewer.PlaneClipper.UpdateClippingPlanes, 0.9)
                viewer.style.AddObserver(
                    "KeyPressEvent",
                    viewer.PlaneClipper.UpdateClippingPlanes, 0.9)
                

    def createViewerCoordsDockWidget(self):
        '''
        Creates a dock widget which contains widgets for displaying the 
        image shown on the viewer, and the coordinate system of the viewer.

        Override to add checkbox for showing and hiding the image overlay
        '''
        super().createViewerCoordsDockWidget()
        overlay_checkbox = QCheckBox("Show Image Overlay")
        overlay_checkbox.setChecked(True)
        overlay_checkbox.setVisible(False)
 


# For running example window -----------------------------------------------------------


def create_main_window():
    window = ViewerMainWindow("Test Viewer Main Window", 'Test Viewer Main Window')
    return window


def main():
    app = QApplication(sys.argv)
    window = create_main_window()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
