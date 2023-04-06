import json
import os
import shutil
import sys
import tempfile
import time
import zipfile
from datetime import datetime
from functools import partial
from pathlib import Path

# Import linking class to join 2D and 3D viewers
import ccpi.viewer.viewerLinker as vlink
import h5py
import numpy as np
import qdarkstyle
import vtk
from ccpi.viewer import viewer2D, viewer3D
from ccpi.viewer.CILViewer import CILViewer
from ccpi.viewer.CILViewer2D import CILViewer2D
from ccpi.viewer.iviewer import SingleViewerCenterWidget
from ccpi.viewer.QCILViewerWidget import QCILDockableWidget, QCILViewerWidget
# from gui.settings_window import create_settings_window
from ccpi.viewer.utils import Converter, cilPlaneClipper
from ccpi.viewer.utils.conversion import Converter, cilNumpyMETAImageWriter
# , QCILViewerWidget
from ccpi.viewer.utils.hdf5_io import HDF5Reader
from ccpi.viewer.utils.io import ImageReader
from eqt.threading import Worker
from eqt.ui import FormDialog
from eqt.ui.SessionDialogs import AppSettingsDialog, ErrorDialog
from eqt.ui.SessionMainWindow import SessionMainWindow
from eqt.ui.UIFormWidget import FormDockWidget, UIFormFactory
from eqt.ui.UIStackedWidget import StackedWidgetFactory
# from eqt.ui.UIFormWidget import UIFormFactory
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import QRegExp, QSettings, Qt, QThreadPool
from PySide2.QtGui import QCloseEvent, QKeySequence, QRegExpValidator
from PySide2.QtWidgets import (QAction, QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDockWidget,
                               QDoubleSpinBox, QFileDialog, QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox,
                               QProgressDialog, QPushButton, QSpinBox, QStackedWidget, QTabWidget)

# TODO: auto plane clipping on viewers


class ViewerMainWindow(SessionMainWindow):
    ''' Creates a window which is designed to house one or more viewers.
    Note: does not create a viewer as we don't know whether the user would like it to exist in a
    dockwidget or central widget
    Instead it creates a main window with many of the tools needed for a window
    that will house a viewer. 
    
    Assumes that at least one viewer is present, saved as self.viewer1
    '''

    def __init__(self,
                 title="ViewerMainWindow",
                 app_name=None,
                 settings_name=None,
                 organisation_name=None,
                 viewer1_type=None,
                 viewer2_type=None,
                 *args,
                 **kwargs):

        # TODO: are viewer types needed?
        super(ViewerMainWindow, self).__init__(title,
                                               app_name,
                                               settings_name=settings_name,
                                               organisation_name=organisation_name)

        self.default_downsampled_size = 512**3

        self.createViewerCoordsDockWidget()
        # could get rid of this:
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.viewer_coords_dock)

        self.viewer1 = None
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
        current settings of the app'''
        super().setAppSettingsDialogWidgets(dialog)
        sw = dialog.widgets

        if self.settings.value('copy_files') is not None:
            sw['copy_files_checkbox_field'].setChecked(int(self.settings.value('copy_files')))
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
        settings to the QSettings object.'''
        super().onAppSettingsDialogAccepted(settings_dialog)

        if settings_dialog.widgets['copy_files_checkbox_field'].isChecked():
            self.settings.setValue("copy_files", 1)
        else:
            self.settings.setValue("copy_files", 0)

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
            raw_dialog.Ok.clicked.connect(lambda: self._get_raw_attrs_from_dialog(raw_dialog))
            raw_dialog.exec_()
        elif file_extension in ['.nxs', '.h5', '.hdf5']:
            raw_dialog = HDF5InputDialog(self, file)
            raw_dialog.Ok.clicked.connect(lambda: self._get_hdf5_attrs_from_dialog(raw_dialog))
            raw_dialog.exec_()

        self.input_dataset_file = file
        if label is not None:
            label.setText(os.path.basename(file))

        return file, self.raw_attrs, self.hdf5_attrs

    def _get_raw_attrs_from_dialog(self, dialog):
        print("got the raw attrs")
        self.raw_attrs = dialog.get_raw_attrs()
        dialog.close()

    def _get_hdf5_attrs_from_dialog(self, dialog):
        print("got the hdf5 attrs")
        self.hdf5_attrs = dialog.getHDF5Attributes()
        dialog.close()

    def createViewerCoordsDockWidget(self):
        '''
        Creates a dock widget which contains widgets for displaying the 
        image shown on the viewer, and the coordinate system of the viewer.
        '''
        dock = ViewerCoordsDockWidget(self)
        self.viewer_coords_dock = dock
        dock.getWidgets()['coords_combo_field'].currentIndexChanged.connect(
            lambda: self.updateViewerCoords(viewer=self.viewer1))

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
        image_reader_worker.signals.error.connect(self.process_error_dialog)

    def process_error_dialog(self, error, **kwargs):
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
                if viewer == self.viewer1:
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


class ViewerCoordsDockWidget(FormDockWidget):
    ''' This is the dockwidget which
    shows the original and downsampled image
    size and the user can select whether coordinates
    are displayed in system of original or downsampled image'''

    def __init__(self, parent):
        super(ViewerCoordsDockWidget, self).__init__(parent)

        form = self.widget()

        viewer_coords_widgets = {}

        self.viewers = []

        viewer_coords_widgets['image'] = QLabel()
        viewer_coords_widgets['image'].setText("Display image: ")

        viewer_coords_widgets['image_combobox'] = QComboBox()
        viewer_coords_widgets['image_combobox'].setEnabled(False)
        form.addWidget(viewer_coords_widgets['image_combobox'], viewer_coords_widgets['image'], 'image')

        viewer_coords_widgets['coords_info'] = QLabel()
        viewer_coords_widgets['coords_info'].setText(
            "The viewer displays a downsampled image for visualisation purposes: ")
        viewer_coords_widgets['coords_info'].setVisible(False)

        form.addSpanningWidget(viewer_coords_widgets['coords_info'], 'coords_info')

        form.addWidget(QLabel(""), QLabel("Loaded Image Size: "), 'loaded_image_dims')

        viewer_coords_widgets['displayed_image_dims_label'] = QLabel()
        viewer_coords_widgets['displayed_image_dims_label'].setText("Displayed Image Size: ")
        viewer_coords_widgets['displayed_image_dims_label'].setVisible(False)

        viewer_coords_widgets['displayed_image_dims_field'] = QLabel()
        viewer_coords_widgets['displayed_image_dims_field'].setText("")
        viewer_coords_widgets['displayed_image_dims_field'].setVisible(False)

        form.addWidget(viewer_coords_widgets['displayed_image_dims_field'],
                       viewer_coords_widgets['displayed_image_dims_label'], 'displayed_image_dims')

        viewer_coords_widgets['coords'] = QLabel()
        viewer_coords_widgets['coords'].setText("Display viewer coordinates in: ")

        viewer_coords_widgets['coords_combo'] = QComboBox()
        viewer_coords_widgets['coords_combo'].addItems(["Loaded Image", "Downsampled Image"])
        viewer_coords_widgets['coords_combo'].setEnabled(False)
        form.addWidget(viewer_coords_widgets['coords_combo'], viewer_coords_widgets['coords'], 'coords_combo')

        viewer_coords_widgets['coords_warning'] = QLabel()
        viewer_coords_widgets['coords_warning'].setText("Warning: These coordinates are approximate.")
        viewer_coords_widgets['coords_warning'].setVisible(False)

        form.addSpanningWidget(viewer_coords_widgets['coords_warning'], 'coords_warning')

    def setViewers(self, viewers):
        ''' Set the viewers which this dock widget will display information for.
        
        Parameters
        ----------
        viewers : list of CILViewer2D and/or CILViewer3D
            The viewers which this dock widget will display information for.'''
        self.viewers = viewers


class ViewerSettingsDialog(AppSettingsDialog):
    ''' This is a dialog window which allows the user to set:
    - whether they would like copies of the images to be saved in the session
    - maximum size to downsample images to for display
    - Whether to use GPU for volume rendering
    '''

    def __init__(self, parent):
        super(ViewerSettingsDialog, self).__init__(parent)

        copy_files_checkbox = QCheckBox("Allow a copy of the image files to be stored. ")

        self.addSpanningWidget(copy_files_checkbox, 'copy_files_checkbox')

        vis_size = QLabel("Maximum downsampled image size (GB): ")
        vis_size_entry = QDoubleSpinBox()
        vis_size_entry.setMaximum(64.0)
        vis_size_entry.setMinimum(0.01)
        vis_size_entry.setSingleStep(0.01)

        self.addWidget(vis_size_entry, vis_size, 'vis_size')

        self.formWidget.addSeparator('adv_separator')

        self.formWidget.addTitle(QLabel("Advanced Settings"), 'adv_settings_title')

        gpu_checkbox = QCheckBox("Use GPU for volume render. (Recommended) ")

        self.addSpanningWidget(gpu_checkbox, 'gpu_checkbox')


class RawInputDialog(FormDialog):

    def __init__(self, parent, fname):
        super(RawInputDialog, self).__init__(parent, fname)
        title = "Config for " + os.path.basename(fname)
        self.setWindowTitle(title)
        fw = self.formWidget

        # dimensionality:
        dimensionalityLabel = QLabel("Dimensionality")
        dimensionalityValue = QComboBox()
        dimensionalityValue.addItems(["3D", "2D"])
        dimensionalityValue.setCurrentIndex(0)
        fw.addWidget(dimensionalityValue, dimensionalityLabel, "dimensionality")

        validator = QtGui.QIntValidator()

        # Entry for size of dimensions:
        for dim in ['X', 'Y', 'Z']:
            ValueEntry = QLineEdit()
            ValueEntry.setValidator(validator)
            ValueEntry.setText("0")
            Label = QLabel("Size {}".format(dim))
            fw.addWidget(ValueEntry, Label, 'dim_{}'.format(dim))

        dimensionalityValue.currentIndexChanged.connect(
            lambda: fw.widgets['dim_Z_field'].setEnabled(True)
            if fw.widgets['dimensionality_field'].currentIndex() == 0 else fw.widgets['dim_Z_field'].setEnabled(False))

        # Data Type
        dtypeLabel = QLabel("Data Type")
        dtypeValue = QComboBox()
        dtypeValue.addItems(["int8", "uint8", "int16", "uint16"])
        dtypeValue.setCurrentIndex(1)
        fw.addWidget(dtypeValue, dtypeLabel, 'dtype')

        # Endianness
        endiannesLabel = QLabel("Byte Ordering")
        endiannes = QComboBox()
        endiannes.addItems(["Big Endian", "Little Endian"])
        endiannes.setCurrentIndex(1)
        fw.addWidget(endiannes, endiannesLabel, 'endianness')

        # Fortran Ordering
        fortranLabel = QLabel("Fortran Ordering")
        fortranOrder = QComboBox()
        fortranOrder.addItems(["Fortran Order: XYZ", "C Order: ZYX"])
        fortranOrder.setCurrentIndex(0)
        fw.addWidget(fortranOrder, fortranLabel, "is_fortran")

        self.setLayout(fw.uiElements['verticalLayout'])

    def get_raw_attrs(self):
        raw_attrs = {}
        widgets = self.formWidget.widgets
        dimensionality = [3, 2][widgets['dimensionality_field'].currentIndex()]
        dims = []
        dims.append(int(widgets['dim_X_field'].text()))
        dims.append(int(widgets['dim_Y_field'].text()))
        if dimensionality == 3:
            dims.append(int(widgets['dim_Z_field'].text()))

        raw_attrs['shape'] = dims
        raw_attrs['is_fortran'] = not bool(widgets['is_fortran_field'].currentIndex())
        raw_attrs['is_big_endian'] = not bool(widgets['endianness_field'].currentIndex())
        raw_attrs['typecode'] = widgets['dtype_field'].currentText()

        return raw_attrs


class HDF5InputDialog(FormDialog):
    '''
    This is a dialog window which allows the user to set:
    - the dataset name
    - whether the Z axis should be downsampled (should not be done for acquisition data)
    
    For selecting the dataset name, this dialog uses a table widget to display the
    contents of the HDF5 file.
    '''

    def __init__(self, parent, fname):
        super(HDF5InputDialog, self).__init__(parent, fname)
        title = "Config for " + os.path.basename(fname)
        self.file_name = fname
        self.setWindowTitle(title)
        fw = self.formWidget

        # Browser for dataset name: --------------------------------------
        # create input text for starting group
        hl, _, line_edit, push_button = self.createLineEditForDatasetName()

        # set the focus on the Browse button
        push_button.setDefault(True)
        # create table widget
        tw = self.createTableWidget()

        dataset_selector_widget = QtWidgets.QWidget()

        vl = QtWidgets.QVBoxLayout()

        # add Widgets to layout
        vl.addLayout(hl)
        vl.addWidget(push_button)
        vl.addWidget(tw)

        dataset_selector_widget.setLayout(vl)

        fw.addSpanningWidget(QLabel("Select Dataset:"), 'dataset_selector_title')

        fw.addSpanningWidget(dataset_selector_widget, 'dataset_selector_widget')

        self.tableWidget = tw
        self.push_button = push_button
        self.line_edit = line_edit

        # ---------------------------------------------------------------

        fw.addSeparator('dataset_selector_separator')

        # dimensionality:
        datasetLabel = QLabel("Dataset Name")
        valueEntry = QLineEdit()
        valueEntry.setEnabled(False)
        fw.addWidget(valueEntry, datasetLabel, "dataset_name")
        self.line_edit.textChanged.connect(self.datasetLineEditChanged)

        # is it Acquisition Data?
        dtypeLabel = QLabel("Resample on Z Axis: ")
        dtypeValue = QComboBox()
        dtypeValue.addItems(["False", "True"])
        fw.addWidget(dtypeValue, dtypeLabel, 'resample_z')

        self.Ok.clicked.connect(self.onOkClicked)

        self.setDefaultDatasetName()

    def setDefaultDatasetName(self):
        '''
        Set the default dataset name to the first entry, as dictated by the
        NXTomo standard, and also CIL's NEXUSDataReader/Writer standard.
        Or if that does not exist in the file, set the default to the root group.
        '''
        nxtomo_dataset_name = "/entry1/tomo_entry/data/data"
        # check if the dataset exists:
        with h5py.File(self.file_name, 'r') as f:

            if nxtomo_dataset_name in f:
                obj = f[nxtomo_dataset_name]
                if isinstance(obj, h5py._hl.dataset.Dataset):
                    self.current_group = nxtomo_dataset_name
                    self.line_edit.setText(nxtomo_dataset_name)
                    return
        # if the dataset does not exist, set the default to the root group:
        self.current_group = '/'
        self.line_edit.setText(self.current_group)

    def onOkClicked(self):
        ''' Will need to override this to add further methods
        when the OK button is clicked.
        
        This checks if the dataset name is valid.'''
        dataset_name = self.widgets['dataset_name_field'].text()
        with h5py.File(self.file_name, 'r') as f:
            try:
                obj = f[dataset_name]
            except:
                error_dialog = ErrorDialog(self, "Error", "Could not open: " + dataset_name)
                error_dialog.open()
                return

            if not isinstance(obj, h5py._hl.dataset.Dataset):
                error_dialog = ErrorDialog(self, "Error", "Not a dataset: " + dataset_name)
                error_dialog.open()
                return

    def getHDF5Attributes(self):
        '''
        Returns a dictionary of attributes required for reading the HDF5 file.

        These are the attributes set by the user in this dialog.
        '''
        hdf5_attrs = {}
        widgets = self.formWidget.widgets

        hdf5_attrs['dataset_name'] = widgets['dataset_name_field'].text()
        hdf5_attrs['resample_z'] = bool(widgets['resample_z_field'].currentIndex())

        return hdf5_attrs

    def createTableWidget(self):
        '''
        Create a table widget to display the contents of the HDF5 file.
        '''
        tableWidget = QtWidgets.QTableWidget()
        tableWidget.itemDoubleClicked.connect(self.fillLineEditWithDoubleClickedTableItem)
        tableWidget.setColumnWidth(1, 40)
        header = tableWidget.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        return tableWidget

    def createLineEditForDatasetName(self):
        '''
        Create a line edit for the user to enter the dataset name.
        '''
        pb = QtWidgets.QPushButton()
        pb.setText("Browse for Dataset...")
        pb.clicked.connect(lambda: self.descendHDF5AndFillTable())

        up = QtWidgets.QPushButton()
        up.setIcon(QtWidgets.QApplication.style().standardPixmap((QtWidgets.QStyle.SP_ArrowUp)))
        up.clicked.connect(lambda: self.goToParentGroup())
        up.setFixedSize(QtCore.QSize(30, 30))

        le = QtWidgets.QLineEdit(self)
        le.returnPressed.connect(lambda: self.descendHDF5AndFillTable())
        le.setClearButtonEnabled(True)

        hl = QtWidgets.QHBoxLayout()
        hl.addWidget(up)
        hl.addWidget(le)

        return hl, up, le, pb

    def datasetLineEditChanged(self, text):
        '''
        This method is called when the text in the line edit is changed.
        '''
        self.widgets['dataset_name_field'].setText(text)

    def fillLineEditWithDoubleClickedTableItem(self, item):
        '''
        This method is called when a table item is double clicked.
        It will fill the line edit with the path to the selected item.
        It will then descend into the selected item and fill the table with
        the contents of the selected item.
        '''
        row = item.row()
        fsitem = self.tableWidget.item(row, 0)
        new_group = fsitem.text()
        current_group = self.line_edit.text()
        with h5py.File(self.file_name, 'r') as f:
            # Try to use the current group entered in the line edit
            # if it does not exist, use the current group saved to memory,
            # which was the last group that was successfully opened.
            try:
                f[current_group]
            except KeyError:
                current_group = self.current_group

            new_path = current_group + "/" + fsitem.text()

            if new_group in f[current_group]:
                self.line_edit.setText(new_path)
                self.current_group = new_path
                self.descendHDF5AndFillTable()
            else:
                error_dialog = ErrorDialog(
                    self, "Error", "The selected item could not be opened.",
                    "f{new_path} either does not exist, or is not a group or dataset, so can't be opened.")
                error_dialog.open()

    def descendHDF5AndFillTable(self):
        '''
        This descends into the HDF5 file and fills the table with the contents
        of the group.
        '''
        # set OverrideCursor to WaitCursor
        QtGui.QGuiApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        group = self.line_edit.text()

        with h5py.File(self.file_name, 'r') as f:
            try:
                obj = f[group]
            except:
                error_dialog = ErrorDialog(self, "Error", "Could not open group: " + group)
                error_dialog.open()
                QtGui.QGuiApplication.restoreOverrideCursor()
                return

            list_of_items = []

            if type(obj) in [h5py._hl.group.Group, h5py._hl.files.File]:
                for key in obj.keys():
                    list_of_items.append((key, str(obj[key])))
            elif isinstance(obj, h5py._hl.dataset.Dataset):
                for key in obj.attrs.keys():
                    list_of_items.append((key, obj.attrs[key]))

        self.loadIntoTableWidget(list_of_items)
        # restore OverrideCursor
        QtGui.QGuiApplication.restoreOverrideCursor()

    def loadIntoTableWidget(self, data):
        '''
        This loads the data into the table widget.
        '''
        if len(data) <= 0:
            return
        self.tableWidget.setRowCount(len(data))
        self.tableWidget.setColumnCount(len(data[0]))
        for i, v in enumerate(data):
            for j, w in enumerate(v):
                item = QtWidgets.QTableWidgetItem(str(w))
                item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                if j == 1:
                    item.setToolTip(str(w))
                self.tableWidget.setItem(i, j, item)

        self.tableWidget.setHorizontalHeaderLabels(['Name', 'Contents'])

        self.tableWidget.sortItems(1, order=QtCore.Qt.AscendingOrder)
        self.tableWidget.resizeColumnsToContents()

    def goToParentGroup(self):
        '''
        This method is called when the up button is clicked.
        It will go to the parent group of the current group.
        '''
        le = self.line_edit
        parent_group = self.getCurrentParentGroup()
        le.setText(str(parent_group))
        self.current_group = parent_group
        self.descendHDF5AndFillTable()

    def getCurrentGroup(self):
        '''
        This method returns the current group.
        '''
        return self.current_group

    def getCurrentParentGroup(self):
        '''
        This method returns the parent group of the current group.
        '''
        current_group = self.getCurrentGroup()
        if current_group != "/" and current_group != "//" and current_group != "":
            item_to_remove = "/" + current_group.split("/")[-1]
            parent_group = current_group[:-len(item_to_remove)]
        else:
            parent_group = current_group

        return parent_group


# For running example window -----------------------------------------------------------


def create_main_window():
    window = ViewerMainWindow("Test Viewer Main Window", 'Test Viewer Main Window')
    return window


def main():
    app = QApplication(sys.argv)
    window = create_main_window()
    window.show()
    # r = RawInputDialog(window, 'fname')
    # r.show()
    # print(r.get_raw_attrs())
    app.exec_()


if __name__ == "__main__":
    main()
