import sys
import vtk
from PySide2 import QtCore, QtWidgets
from ccpi.viewer import viewer2D, viewer3D
from ccpi.viewer.QCILViewerWidget import QCILViewerWidget
import ccpi.viewer.viewerLinker as vlink
from ccpi.viewer.utils.conversion import Converter
import numpy as np

import json
import os
import shutil
import tempfile
import time
import zipfile
from datetime import datetime
from functools import partial
from pathlib import Path

# Import linking class to join 2D and 3D viewers
import ccpi.viewer.viewerLinker as vlink
import h5py
import qdarkstyle
import vtk
from ccpi.viewer import viewer2D, viewer3D
from ccpi.viewer.iviewer import SingleViewerCenterWidget
from ccpi.viewer.QCILViewerWidget import QCILDockableWidget
# from gui.settings_dialog import create_settings_dialog
from ccpi.viewer.utils import Converter, cilPlaneClipper
# , QCILViewerWidget
from ccpi.viewer.utils.hdf5_io import HDF5Reader
from eqt.threading import Worker
from eqt.ui import FormDialog
from eqt.ui.UIFormWidget import UIFormFactory
from eqt.ui.UIStackedWidget import StackedWidgetFactory
# from eqt.ui.UIFormWidget import UIFormFactory
from PySide2 import QtCore
from PySide2.QtCore import QRegExp, QSettings, Qt, QThreadPool
from PySide2.QtGui import QCloseEvent, QKeySequence, QRegExpValidator
from PySide2.QtWidgets import (QAction,  QApplication, QCheckBox, QComboBox, QDockWidget,
                               QFileDialog, QLabel, QLineEdit, QMainWindow,
                               QMenu, QMessageBox, QProgressDialog,
                               QPushButton, QSpinBox, QStackedWidget,
                               QTabWidget)

from eqt.ui.UIMainWindow import MainWindow, SettingsDialog

from eqt.ui import  UIFormFactory
from PySide2.QtWidgets import (QCheckBox, QDoubleSpinBox, QLabel, QDialog, QDialogButtonBox)

from PySide2.QtCore import Qt

from eqt.ui import UIFormFactory   

from eqt.threading.QtThreading import ErrorObserver

#from ccpi.viewer.standalone_viewer import TwoLinkedViewersCenterWidget, SingleViewerCenterWidget


# TODO: methods to create the viewers but not place them
# TODO: auto plane clipping on viewers

class ViewerMainWindow(MainWindow):

    def __init__(self, title="", viewer2_type = None, *args, **kwargs): #viewer1_type
        MainWindow.__init__(self, title)

        # Note: does not create a viewer as we don't know whether the user would like it to exist in a
        # dockwidget or central widget
        
        # self.setUp(viewer1_type, viewer2_type, *args, **kwargs)
        # self.show()
        self.e = ErrorObserver() # only needed with old io module


        self.CreateViewerSettingsPanel()
        # could get rid of this:
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.viewer_settings_dock)

        self.viewer_2D = None

        print("The settings: ", self.settings, self.settings.allKeys())

    # def setUp(self, viewer1_type, viewer2_type = None, *args, **kwargs):
    #     '''
    #     viewer1_type: '2D' or '3D'
    #     viewer2_type: '2D', '3D' or None - if None, only one viewer is displayed
    #     '''

    #     if viewer1_type == '2D':
    #         viewer1 = viewer2D
    #     elif viewer1_type == '3D':
    #         viewer1 = viewer3D

    #     if viewer2_type is None:
    #         window = SingleViewerCenterWidget(viewer=viewer1)        
    #     else:
    #         if viewer2_type == '2D':
    #             viewer2 = viewer2D
    #         elif viewer2_type == '3D':
    #             viewer2 = viewer3D

    #         window = TwoLinkedViewersCenterWidget(viewer1=viewer1, viewer2=viewer2)

    #     self.SetCe


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
            sw['vis_size_field'].setValue(float(self.settings.value("vis_size")))
        else:
            sw['vis_size_field'].setValue(1.0)

        if self.settings.value("gpu_size") is not None:
            sw['gpu_size_field'].setValue(float(self.settings.value("gpu_size")))
        else:
            sw['gpu_size_field'].setValue(1.0)
        

    def settings_dialog_accept(self, settings_dialog):
        MainWindow.settings_dialog_accept(self, settings_dialog)

        if settings_dialog.fw.widgets['copy_files_checkbox_field'].isChecked():
            self.copy_files = 1 # save for this session
            self.settings.setValue("copy_files", 1) #save for next time we open app
        else:
            self.copy_files = 0
            self.settings.setValue("copy_files", 0)

        # TODO: use in the case we have a 3D viewer

        # if self.gpu_checkbox.isChecked():
        #     self.parent.settings.setValue("volume_mapper", "gpu")
        #     #self.parent.vis_widget_3D.volume_mapper = vtk.vtkSmartVolumeMapper()
        # else:
        #     self.parent.settings.setValue("volume_mapper", "cpu")

        self.settings.setValue("gpu_size", float(settings_dialog.fw.widgets['gpu_size_field'].value()))
        self.settings.setValue("vis_size", float(settings_dialog.fw.widgets['vis_size_field'].value()))

    def select_image(self, label=None):
        #print("In select image")
        dialogue = QFileDialog()
        file = dialogue.getOpenFileName(self, "Load Images")[0]
        file_extension = Path(file).suffix.lower()
        if 'tif' in file_extension:
            print('tif ', file)
            file = os.path.dirname(file)
        self.input_dataset_file = file
        if label is not None:
            label.setText(os.path.basename(file))

        return file


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
        form.addWidget(vs_widgets['coords_combobox'], vs_widgets['coords_label'], 'cords_combo')

        vs_widgets['coords_warning_label'] = QLabel()
        vs_widgets['coords_warning_label'].setText(
            "Warning: These coordinates are approximate.")
        vs_widgets['coords_warning_label'].setVisible(False)

        form.addSpanningWidget(vs_widgets['coords_warning_label'], 'coords_warning')

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

        copy_files_checkbox = QCheckBox("Allow a copy of the image files to be stored. ")

        fw.addSpanningWidget(copy_files_checkbox, 'copy_files_checkbox')
        
        vis_size_label = QLabel("Maximum downsampled image size (GB): ")
        vis_size_entry = QDoubleSpinBox()
        vis_size_entry.setMaximum(64.0)
        vis_size_entry.setMinimum(0.01)
        vis_size_entry.setSingleStep(0.01)

        fw.addWidget(vis_size_entry, vis_size_label, 'vis_size')

        fw.addSeparator('adv_separator')

        fw.addTitle(QLabel("Advanced Settings"), 'adv_settings_title')

        fw.addSpanningWidget(QLabel("Please set the size of your GPU memory."), 'gpu_size_title')
        
        gpu_size_label = QLabel("GPU Memory (GB): ")
        gpu_size_entry = QDoubleSpinBox()
        
        gpu_size_entry.setMaximum(64.0)
        gpu_size_entry.setMinimum(0.00)
        gpu_size_entry.setSingleStep(0.01)
        fw.addWidget(gpu_size_entry, gpu_size_label, 'gpu_size')

        #TODO later when we have a 3D renderer - change volume render settings:
        # self.gpu_checkbox = QCheckBox("Use GPU for volume render. (Recommended) ")
        # self.gpu_checkbox.setChecked(True) #gpu is default
        # if self.parent.settings.value("volume_mapper") == "cpu":
        #     self.gpu_checkbox.setChecked(False)
        

# For running example window -----------------------------------------------------------

def create_main_window():
    window = ViewerMainWindow("Test Viewer Main Window", '2D')
    return window


def main():
    app = QApplication(sys.argv)
    window = create_main_window()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()