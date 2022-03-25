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
# from gui.settings_dialog import create_settings_dialog
from ccpi.viewer.utils import Converter, cilPlaneClipper
from ccpi.viewer.utils.conversion import Converter
# , QCILViewerWidget
from ccpi.viewer.utils.hdf5_io import HDF5Reader
from eqt.threading import Worker
from eqt.threading.QtThreading import ErrorObserver
from eqt.ui import FormDialog, UIFormFactory
from eqt.ui.UIFormWidget import UIFormFactory
from eqt.ui.UIMainWindow import MainWindow, SettingsDialog
from eqt.ui.UIStackedWidget import StackedWidgetFactory
# from eqt.ui.UIFormWidget import UIFormFactory
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import QRegExp, QSettings, Qt, QThreadPool
from PySide2.QtGui import QCloseEvent, QKeySequence, QRegExpValidator
from PySide2.QtWidgets import (QAction, QApplication, QCheckBox, QComboBox,
                               QDialog, QDialogButtonBox, QDockWidget,
                               QDoubleSpinBox, QFileDialog, QLabel, QLineEdit,
                               QMainWindow, QMenu, QMessageBox,
                               QProgressDialog, QPushButton, QSpinBox,
                               QStackedWidget, QTabWidget)

#from ccpi.viewer.standalone_viewer import TwoLinkedViewersCenterWidget, SingleViewerCenterWidget


# TODO: methods to create the viewers but not place them
# TODO: auto plane clipping on viewers

class ViewerMainWindow(MainWindow):

    def __init__(self, title="", viewer2_type=None, *args, **kwargs):  # viewer1_type
        MainWindow.__init__(self, title)

        ''' Creates a window which is designed to house one or more viewers.
        Note: does not create a viewer as we don't know whether the user would like it to exist in a
        dockwidget or central widget
        Instead it creates a main window with many of the tools needed for a window
        that will house a viewer. '''

        self.e = ErrorObserver()  # only needed with old io module

        self.CreateViewerSettingsPanel()
        # could get rid of this:
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea,
                           self.viewer_settings_dock)

        self.viewer_2D = None

        print("The settings: ", self.settings, self.settings.allKeys())


    def open_settings_dialog(self):
        settings_dialog = ViewerSettingsDialog(self)
        self.setup_settings_dialog(settings_dialog)
        settings_dialog.show()

    def setup_settings_dialog(self, settings_dialog):
        MainWindow.setup_settings_dialog(self, settings_dialog)
        sw = settings_dialog.fw.widgets
        if hasattr(self, 'copy_files'):
            sw['copy_files_checkbox_field'].setChecked(self.copy_files)
        if self.settings.value("vis_size") is not None:
            sw['vis_size_field'].setValue(
                float(self.settings.value("vis_size")))
        else:
            sw['vis_size_field'].setValue(1.0)

        if self.settings.value("gpu_size") is not None:
            sw['gpu_size_field'].setValue(
                float(self.settings.value("gpu_size")))
        else:
            sw['gpu_size_field'].setValue(1.0)

    def settings_dialog_accept(self, settings_dialog):
        MainWindow.settings_dialog_accept(self, settings_dialog)

        if settings_dialog.fw.widgets['copy_files_checkbox_field'].isChecked():
            self.copy_files = 1  # save for this session
            # save for next time we open app
            self.settings.setValue("copy_files", 1)
        else:
            self.copy_files = 0
            self.settings.setValue("copy_files", 0)

        # TODO: use in the case we have a 3D viewer

        # if self.gpu_checkbox.isChecked():
        #     self.parent.settings.setValue("volume_mapper", "gpu")
        #     #self.parent.vis_widget_3D.volume_mapper = vtk.vtkSmartVolumeMapper()
        # else:
        #     self.parent.settings.setValue("volume_mapper", "cpu")

        self.settings.setValue("gpu_size", float(
            settings_dialog.fw.widgets['gpu_size_field'].value()))
        self.settings.setValue("vis_size", float(
            settings_dialog.fw.widgets['vis_size_field'].value()))

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

    def CreateViewerSettingsPanel(self):
        print("make panel")
        dock = UIFormFactory.getQDockWidget()
        form = dock.widget()
        self.viewer_settings_dock = dock

        vs_widgets = {}

        vs_widgets['coords_info_label'] = QLabel()
        vs_widgets['coords_info_label'].setText(
            "The viewer displays a downsampled image for visualisation purposes: ")
        vs_widgets['coords_info_label'].setVisible(False)

        form.addSpanningWidget(vs_widgets['coords_info_label'], 'coords_info')

        vs_widgets['loaded_image_dims_label'] = QLabel()
        vs_widgets['loaded_image_dims_label'].setText("Loaded Image Size: ")
        vs_widgets['loaded_image_dims_label'].setVisible(True)

        vs_widgets['loaded_image_dims_value'] = QLabel()
        vs_widgets['loaded_image_dims_value'].setText("")
        vs_widgets['loaded_image_dims_value'].setVisible(False)

        form.addWidget(vs_widgets['loaded_image_dims_value'],
                       vs_widgets['loaded_image_dims_label'],
                       'loaded_image_dims')

        vs_widgets['displayed_image_dims_label'] = QLabel()
        vs_widgets['displayed_image_dims_label'].setText(
            "Displayed Image Size: ")
        vs_widgets['displayed_image_dims_label'].setVisible(False)

        vs_widgets['displayed_image_dims_value'] = QLabel()
        vs_widgets['displayed_image_dims_value'].setText("")
        vs_widgets['displayed_image_dims_value'].setVisible(False)

        form.addWidget(vs_widgets['displayed_image_dims_value'],
                       vs_widgets['displayed_image_dims_label'],
                       'displayed_image_dims')

        vs_widgets['coords_label'] = QLabel()
        vs_widgets['coords_label'].setText("Display viewer coordinates in: ")

        vs_widgets['coords_combobox'] = QComboBox()
        vs_widgets['coords_combobox'].addItems(
            ["Loaded Image", "Downsampled Image"])
        vs_widgets['coords_combobox'].setEnabled(False)
        vs_widgets['coords_combobox'].currentIndexChanged.connect(
            self.updateCoordinates)
        form.addWidget(vs_widgets['coords_combobox'],
                       vs_widgets['coords_label'], 'cords_combo')

        vs_widgets['coords_warning_label'] = QLabel()
        vs_widgets['coords_warning_label'].setText(
            "Warning: These coordinates are approximate.")
        vs_widgets['coords_warning_label'].setVisible(False)

        form.addSpanningWidget(
            vs_widgets['coords_warning_label'], 'coords_warning')

        self.visualisation_setting_widgets = vs_widgets

    def updateCoordinates(self):
        vs_widgets = self.visualisation_setting_widgets
        viewer = self.viewer_2D
        if viewer.img3D is not None:
            viewer.setVisualisationDownsampling(self.resample_rate)
            shown_resample_rate = self.resample_rate
            vs_widgets['loaded_image_dims_label'].setVisible(True)
            vs_widgets['loaded_image_dims_value'].setVisible(True)

            if vs_widgets['coords_combobox'].currentIndex() == 0:
                viewer.setDisplayUnsampledCoordinates(True)
                if shown_resample_rate != [1, 1, 1]:
                    vs_widgets['coords_warning_label'].setVisible(True)
                else:
                    vs_widgets['coords_warning_label'].setVisible(False)

            else:
                viewer.setDisplayUnsampledCoordinates(False)
                vs_widgets['coords_warning_label'].setVisible(False)

            viewer.updatePipeline()


class ViewerSettingsDialog(SettingsDialog):

    def __init__(self, parent):
        super(ViewerSettingsDialog, self).__init__(parent)

        fw = self.fw

        copy_files_checkbox = QCheckBox(
            "Allow a copy of the image files to be stored. ")

        fw.addSpanningWidget(copy_files_checkbox, 'copy_files_checkbox')

        vis_size_label = QLabel("Maximum downsampled image size (GB): ")
        vis_size_entry = QDoubleSpinBox()
        vis_size_entry.setMaximum(64.0)
        vis_size_entry.setMinimum(0.01)
        vis_size_entry.setSingleStep(0.01)

        fw.addWidget(vis_size_entry, vis_size_label, 'vis_size')

        fw.addSeparator('adv_separator')

        fw.addTitle(QLabel("Advanced Settings"), 'adv_settings_title')

        fw.addSpanningWidget(
            QLabel("Please set the size of your GPU memory."), 'gpu_size_title')

        gpu_size_label = QLabel("GPU Memory (GB): ")
        gpu_size_entry = QDoubleSpinBox()

        gpu_size_entry.setMaximum(64.0)
        gpu_size_entry.setMinimum(0.00)
        gpu_size_entry.setSingleStep(0.01)
        fw.addWidget(gpu_size_entry, gpu_size_label, 'gpu_size')

        # TODO later when we have a 3D renderer - change volume render settings:
        # self.gpu_checkbox = QCheckBox("Use GPU for volume render. (Recommended) ")
        # self.gpu_checkbox.setChecked(True) #gpu is default
        # if self.parent.settings.value("volume_mapper") == "cpu":
        #     self.gpu_checkbox.setChecked(False)


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
        self.setWindowTitle(title)
        fw = self.formWidget

        # dimensionality:
        datasetLabel = QLabel("Dataset Name")
        valueEntry = QLineEdit()
        valueEntry.setText("entry1/tomo_entry/data/data")
        fw.addWidget(valueEntry, datasetLabel, "dataset_name")

        # is it Acquisition Data?
        dtypeLabel = QLabel("Acquisition Data: ")
        dtypeValue = QComboBox()
        dtypeValue.addItems(["True", "False"])
        fw.addWidget(dtypeValue, dtypeLabel, 'dtype')


    def get_hdf5_attrs(self):
        hdf5_attrs = {}
        widgets = self.formWidget.widgets

        hdf5_attrs['dataset_name'] = widgets['dataset_name_field'].text()
        hdf5_attrs['is_acquisition_data'] = not bool(widgets['dtype_field'].currentIndex())

        return hdf5_attrs

# For running example window -----------------------------------------------------------


def create_main_window():
    window = ViewerMainWindow("Test Viewer Main Window", '2D')
    return window


def main():
    app = QApplication(sys.argv)
    window = create_main_window()
    window.show()
    r = RawInputDialog(window, 'fname')
    r.show()
    print(r.get_raw_attrs())
    app.exec_()


if __name__ == "__main__":
    main()
