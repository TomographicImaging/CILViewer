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
from ccpi.viewer.iviewer import SingleViewerCenterWidget
from ccpi.viewer.QCILViewerWidget import QCILDockableWidget, QCILViewerWidget
from ccpi.viewer.utils import Converter, cilPlaneClipper
from ccpi.viewer.utils.conversion import Converter
from ccpi.viewer.utils.hdf5_io import HDF5Reader
from eqt.ui import FormDialog
from eqt.ui.UIFormWidget import FormDockWidget
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import QRegExp, QSettings, Qt, QThreadPool
from PySide2.QtGui import QCloseEvent, QKeySequence, QRegExpValidator
from PySide2.QtWidgets import (QAction, QApplication, QCheckBox, QComboBox,
                               QDialog, QDialogButtonBox, QDockWidget,
                               QDoubleSpinBox, QFileDialog, QLabel, QLineEdit,
                               QMainWindow, QMenu, QMessageBox,
                               QProgressDialog, QPushButton, QSpinBox,
                               QStackedWidget, QTabWidget)

from eqt.ui.SessionMainWindow import SessionMainWindow
from eqt.ui.SessionDialogs import AppSettingsDialog, ErrorDialog

from ccpi.viewer.utils.hdf5_utils import HDF5_utilities



#from ccpi.viewer.standalone_viewer import TwoLinkedViewersCenterWidget, SingleViewerCenterWidget


# TODO: methods to create the viewers but not place them
# TODO: auto plane clipping on viewers

class ViewerMainWindow(SessionMainWindow):

    ''' Creates a window which is designed to house one or more viewers.
    Note: does not create a viewer as we don't know whether the user would like it to exist in a
    dockwidget or central widget
    Instead it creates a main window with many of the tools needed for a window
    that will house a viewer. '''

    def __init__(self, title="ViewerMainWindow", app_name= None, settings_name=None,
                 organisation_name=None, viewer1_type=None, viewer2_type=None, *args, **kwargs): 
        
        # TODO: are viewer types needed?
        super(ViewerMainWindow, self).__init__(title, app_name, settings_name=settings_name, organisation_name=organisation_name)

        self.default_downsampled_size = 512**3

        self.createViewerCoordsDockWidget()
        # could get rid of this:
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea,
                           self.viewer_coords_dock)

        self.viewer_2D = None

        print("The settings: ", self.settings, self.settings.allKeys())


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
            sw['vis_size_field'].setValue(
                float(self.settings.value("vis_size")))
        else:
            sw['vis_size_field'].setValue(self.getDefaultDownsampledSize()/(1024**3))

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

        self.settings.setValue("vis_size", float(
            settings_dialog.widgets['vis_size_field'].value()))
        
        if settings_dialog.widgets['gpu_checkbox_field'].isChecked():
            self.settings.setValue("volume_mapper", "gpu")
            # TODO: check if this is the right way to do it:
            self.vis_widget_3D.volume_mapper = vtk.vtkSmartVolumeMapper()
        else:
            self.settings.setValue("volume_mapper", "cpu")

    def select_image(self, label=None):
        ''' This selects the images and gets the user to enter
        relevant data, but does not load them on a viewer yet.'''
        dialog = QFileDialog()
        file = dialog.getOpenFileName(self, "Select Images")[0]
        file_extension = Path(file).suffix.lower()
        self.raw_attrs = {}
        self.hdf5_attrs = {}
        print("The file ext: ", file_extension)
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
        self.hdf5_attrs = dialog.get_hdf5_attrs()
        dialog.close()

    def createViewerCoordsDockWidget(self):
        '''
        Creates a dock widget which contains widgets for displaying the 
        image shown on the viewer, and the coordinate system of the viewer.
        '''
        dock = ViewerCoordsDockWidget(self)
        self.viewer_coords_dock = dock
        dock.getWidgets()['coords_combo_field'].currentIndexChanged.connect(self.update_coordinates)


    def update_coordinates(self):
        '''
        Updates the coordinate system of the viewer, and the displayed image
        dimensions.'''
        viewer_coords_widgets = self.viewer_coords_dock.widgets()
        viewer = self.viewer_2D
        if viewer.img3D is not None:
            viewer.setVisualisationDownsampling(self.getTargetImageSize())
            shown_resample_rate = self.getTargetImageSize()
            viewer_coords_widgets['loaded_image_dims_label'].setVisible(True)
            viewer_coords_widgets['loaded_image_dims_value'].setVisible(True)

            if viewer_coords_widgets['coords_combobox'].currentIndex() == 0:
                viewer.setDisplayUnsampledCoordinates(True)
                if shown_resample_rate != [1, 1, 1]:
                    viewer_coords_widgets['coords_warning_label'].setVisible(True)
                else:
                    viewer_coords_widgets['coords_warning_label'].setVisible(False)

            else:
                viewer.setDisplayUnsampledCoordinates(False)
                viewer_coords_widgets['coords_warning_label'].setVisible(False)

            viewer.updatePipeline()

    def getTargetImageSize(self):
        ''' Get the target size for an image to be displayed in bytes.'''
        if self.settings.value("vis_size") is not None:
            target_size = float(self.settings.value("vis_size"))*(1024**3)
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

    # TODO: adding dropdown for file name displayed

    def __init__(self, parent):
        super(ViewerCoordsDockWidget, self).__init__(parent)

        form = self.widget()
        
        viewer_coords_widgets = {}

        viewer_coords_widgets['image_label'] = QLabel()
        viewer_coords_widgets['image_label'].setText("Display image: ")

        viewer_coords_widgets['image_combobox'] = QComboBox()
        viewer_coords_widgets['image_combobox'].setEnabled(False)
        form.addWidget(viewer_coords_widgets['image_combobox'],
                       viewer_coords_widgets['image_label'], 'image')

        viewer_coords_widgets['coords_info_label'] = QLabel()
        viewer_coords_widgets['coords_info_label'].setText(
            "The viewer displays a downsampled image for visualisation purposes: ")
        viewer_coords_widgets['coords_info_label'].setVisible(False)

        form.addSpanningWidget(viewer_coords_widgets['coords_info_label'], 'coords_info')

        viewer_coords_widgets['loaded_image_dims_label'] = QLabel()
        viewer_coords_widgets['loaded_image_dims_label'].setText("Loaded Image Size: ")
        viewer_coords_widgets['loaded_image_dims_label'].setVisible(True)

        viewer_coords_widgets['loaded_image_dims_value'] = QLabel()
        viewer_coords_widgets['loaded_image_dims_value'].setText("")
        viewer_coords_widgets['loaded_image_dims_value'].setVisible(False)

        form.addWidget(viewer_coords_widgets['loaded_image_dims_value'],
                       viewer_coords_widgets['loaded_image_dims_label'],
                       'loaded_image_dims')

        viewer_coords_widgets['displayed_image_dims_label'] = QLabel()
        viewer_coords_widgets['displayed_image_dims_label'].setText(
            "Displayed Image Size: ")
        viewer_coords_widgets['displayed_image_dims_label'].setVisible(False)

        viewer_coords_widgets['displayed_image_dims_value'] = QLabel()
        viewer_coords_widgets['displayed_image_dims_value'].setText("")
        viewer_coords_widgets['displayed_image_dims_value'].setVisible(False)

        form.addWidget(viewer_coords_widgets['displayed_image_dims_value'],
                       viewer_coords_widgets['displayed_image_dims_label'],
                       'displayed_image_dims')

        viewer_coords_widgets['coords_label'] = QLabel()
        viewer_coords_widgets['coords_label'].setText("Display viewer coordinates in: ")

        viewer_coords_widgets['coords_combobox'] = QComboBox()
        viewer_coords_widgets['coords_combobox'].addItems(
            ["Loaded Image", "Downsampled Image"])
        viewer_coords_widgets['coords_combobox'].setEnabled(False)
        form.addWidget(viewer_coords_widgets['coords_combobox'],
                       viewer_coords_widgets['coords_label'], 'coords_combo')

        viewer_coords_widgets['coords_warning_label'] = QLabel()
        viewer_coords_widgets['coords_warning_label'].setText(
            "Warning: These coordinates are approximate.")
        viewer_coords_widgets['coords_warning_label'].setVisible(False)

        form.addSpanningWidget(
            viewer_coords_widgets['coords_warning_label'], 'coords_warning')

class ViewerSettingsDialog(AppSettingsDialog):
    ''' This is a dialog window which allows the user to set:
    - whether they would like copies of the images to be saved in the session
    - maximum size to downsample images to for display
    - Whether to use GPU for volume rendering
    '''

    def __init__(self, parent):
        super(ViewerSettingsDialog, self).__init__(parent)

        copy_files_checkbox = QCheckBox(
            "Allow a copy of the image files to be stored. ")

        self.addSpanningWidget(copy_files_checkbox, 'copy_files_checkbox')

        vis_size_label = QLabel("Maximum downsampled image size (GB): ")
        vis_size_entry = QDoubleSpinBox()
        vis_size_entry.setMaximum(64.0)
        vis_size_entry.setMinimum(0.01)
        vis_size_entry.setSingleStep(0.01)

        self.addWidget(vis_size_entry, vis_size_label, 'vis_size')

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
        fw.addWidget(dimensionalityValue,
                     dimensionalityLabel, "dimensionality")

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
            if fw.widgets['dimensionality_field'].currentIndex() == 0 else
            fw.widgets['dim_Z_field'].setEnabled(False))

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

        raw_attrs['dimensions'] = dims
        raw_attrs['is_fortran'] = not bool(widgets['is_fortran_field'].currentIndex())
        raw_attrs['is_big_endian'] = not bool(widgets['endianness_field'].currentIndex())
        raw_attrs['typecode'] = widgets['dtype_field'].currentText()

        return raw_attrs

class HDF5InputDialog(FormDialog):
    def __init__(self, parent, fname):
        super(HDF5InputDialog, self).__init__(parent, fname)
        title = "Config for " + os.path.basename(fname)
        self.file_name = fname
        self.setWindowTitle(title)
        fw = self.formWidget


        # Browser for dataset name:
        # create input text for starting group
        hl, up, line_edit, push_button= self.createLineEditForDatasetName()

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
        when the OK button is clicked.'''
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
        

    def get_hdf5_attrs(self):
        hdf5_attrs = {}
        widgets = self.formWidget.widgets

        hdf5_attrs['dataset_name'] = widgets['dataset_name_field'].text()
        hdf5_attrs['resample_z'] = bool(widgets['resample_z_field'].currentIndex())

        return hdf5_attrs
    
    def datasetLineEditChanged(self, text):
        self.widgets['dataset_name_field'].setText(text)
    
    def createTableWidget(self):
        tableWidget = QtWidgets.QTableWidget()
        tableWidget.itemDoubleClicked.connect(self.fillLineEditWithDoubleClickedTableItem)
        tableWidget.setColumnWidth(1,40)
        header = tableWidget.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        return tableWidget


    def fillLineEditWithDoubleClickedTableItem(self, item):
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
                error_dialog = ErrorDialog(self, "Error", 
                                "The selected item could not be opened.", "f{new_path} either does not exist, or is not a group or dataset, so can't be opened.")
                error_dialog.open()

    
    def createLineEditForDatasetName(self):        
        pb = QtWidgets.QPushButton()
        pb.setText("Browse for Dataset...")
        pb.clicked.connect(lambda: self.descendHDF5AndFillTable())
        
        up = QtWidgets.QPushButton()
        up.setIcon(QtWidgets.QApplication.style().standardPixmap((QtWidgets.QStyle.SP_ArrowUp)))
        up.clicked.connect(lambda: self.goToParentGroup())
        up.setFixedSize(QtCore.QSize(30,30))
        
        le = QtWidgets.QLineEdit(self)
        le.returnPressed.connect(lambda: self.descendHDF5AndFillTable())
        le.setClearButtonEnabled(True)

        hl = QtWidgets.QHBoxLayout()
        hl.addWidget(up)
        hl.addWidget(le)
        
        return hl, up, le, pb
    
    def descendHDF5AndFillTable(self):
        # load data into table widget
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
        # self.loadIntoTableWidget(ddata)
        # restore OverrideCursor
        QtGui.QGuiApplication.restoreOverrideCursor()

    def loadIntoTableWidget(self, data):
        if len(data) <= 0:
            return
        self.tableWidget.setRowCount(len(data))
        self.tableWidget.setColumnCount(len(data[0]))
        for i, v in enumerate(data):
            for j, w in enumerate(v):
                item = QtWidgets.QTableWidgetItem(str(w))
                item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled);
                if j == 1:
                    item.setToolTip(str(w))
                self.tableWidget.setItem(i, j, item)
                
        self.tableWidget.setHorizontalHeaderLabels(['Name', 'Contents'])
        
        self.tableWidget.sortItems(1, order=QtCore.Qt.AscendingOrder)
        self.tableWidget.resizeColumnsToContents()

    def goToParentGroup(self):
        le = self.line_edit
        parent_group  = self.getCurrentParentGroup()
        le.setText(str(parent_group))
        self.current_group = parent_group
        self.descendHDF5AndFillTable()

    def getCurrentGroup(self):
        return self.current_group
    
    def getCurrentParentGroup(self):
        # how to get the directory above the current one
        current_group = self.getCurrentGroup()
        print("The current group is: ", current_group)
        if current_group != "/" and current_group != "//" and current_group != "":
            print("Removing an item")
            item_to_remove = "/" + current_group.split("/")[-1]
            parent_group = current_group[:-len(item_to_remove)]
        else:
            print("Not removing an item")
            print("The current group is: ", current_group)
            parent_group = current_group

        print("The parent group is: ", parent_group)
        
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
