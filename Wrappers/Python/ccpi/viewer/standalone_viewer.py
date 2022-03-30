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
from ccpi.viewer.CILViewer2D import CILViewer2D
from ccpi.viewer.iviewer import SingleViewerCenterWidget
from ccpi.viewer.QCILViewerWidget import QCILDockableWidget
# from gui.settings_window import create_settings_window
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
from PySide2.QtWidgets import (QAction, QCheckBox, QComboBox, QDockWidget,
                               QFileDialog, QLabel, QLineEdit, QMainWindow,
                               QMenu, QMessageBox, QProgressDialog,
                               QPushButton, QSpinBox, QStackedWidget,
                               QTabWidget)
from qdarkstyle.dark.palette import DarkPalette
from qdarkstyle.light.palette import LightPalette

from eqt.ui.UIMainWindow import MainWindow

from ccpi.viewer.viewer_main_window import ViewerMainWindow

#from ccpi.viewer.utils.io import ImageDataCreator

from ccpi.viewer.utils.io_new import ImageReader

from eqt.threading import Worker

from ccpi.viewer.utils.conversion import cilNumpyMETAImageWriter

# TODO next - get progress from Worker

# TODO: see line 654 in iDVC to get resample rate from returned image from io
# but we will scrap io!
# instead look at how to get the resample rate of downsampled images

class StandaloneViewerMainWindow(ViewerMainWindow):
    def __init__(self, title = "StandaloneViewer", viewer1=viewer2D, viewer2=viewer3D):
        ViewerMainWindow.__init__(self, title)

        self.input_data1 = None
        self.input_data2 = None

        if viewer1 == viewer2D:
            interactor_style1 = vlink.Linked2DInteractorStyle
        elif viewer1 == viewer3D:
            interactor_style1 = vlink.Linked3DInteractorStyle

        if viewer2 == viewer2D:
            interactor_style2 = vlink.Linked2DInteractorStyle
        elif viewer2 == viewer3D:
            interactor_style2 = vlink.Linked3DInteractorStyle

        self.frame1 = QCILViewerWidget(viewer=viewer1, shape=(600,600),
              interactorStyle=interactor_style1)
        self.frame2 = QCILViewerWidget(viewer=viewer2, shape=(600,600),
              interactorStyle=interactor_style2)

        self.viewer_2D = self.frame1.viewer
                
        # Initially link viewers
        self.linkedViewersSetUp()
        self.linker.enable()

        layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight)
        layout.addWidget(self.frame1)
        layout.addWidget(self.frame2)
        
        cw = QtWidgets.QWidget()
        cw.setLayout(layout)
        self.setCentralWidget(cw)
        self.central_widget = cw


    def create_menu(self):
        ViewerMainWindow.create_menu(self)

        # find the settings action which already exists:
        for action in self.file_menu.actions():
            action_name = action.text()
            if 'Settings' in action_name:
                settings_action = action

            
        # insert image selection actions before the settings action:

        image1_action = QAction("Select Image 1", self)
        image1_action.triggered.connect(lambda: self.set_viewer_input(1))
        self.file_menu.insertAction(settings_action, image1_action)

        image2_action = QAction("Select Image 2", self)
        image2_action.triggered.connect(lambda: self.set_viewer_input(2))
        self.file_menu.insertAction(settings_action, image2_action)

    def set_viewer_input(self, input_num=1):
        image_file, raw_image_attrs, hdf5_image_attrs = self.select_image()
        print("The image attrs: ", raw_image_attrs)
        target_size = self.get_target_image_size()
        print("The target size is: ", target_size)
        image_reader = ImageReader(file_name=image_file, target_size=target_size, raw_image_attrs=raw_image_attrs, hdf5_image_attrs=hdf5_image_attrs)
        image_reader_worker = Worker(image_reader.read)
        self.threadpool.start(image_reader_worker)
        if input_num == 1:
            image_reader_worker.signals.result.connect(self.display_image)
        elif input_num == 2:
            # This makes sure the result ends up as image2 not image1 when we call display_image
            image_reader_worker.signals.result.connect(partial(self.display_image, None))
        
    
    def linkedViewersSetUp(self):
        v1 = self.frame1.viewer
        v2 = self.frame2.viewer
        self.linker = vlink.ViewerLinker(v1, v2)
        self.linker.setLinkPan(True)
        self.linker.setLinkZoom(True)
        self.linker.setLinkWindowLevel(True)
        self.linker.setLinkSlice(True)

    def get_downsampled_size(self):
        # original_image_attrs
        # TODO: here we need to get the size the image was downsampled to
        # and original image size
        # and feed in necessary data to viewer so that our dropdown works
        # see what happens in idvc
        pass


    def display_image(self, image1=None, image2=None, **kwargs):
        if image1 is not None:
            self.frame1.viewer.setInputData(image1)
            self.frame2.viewer.setInputData(image1)
            self.input_data1 = image1
            self.viewer_coords_dock.getWidgets()['coords_combo_field'].setEnabled(True)
        if image2 is not None:
            viewers = [self.frame1.viewer, self.frame2.viewer]
            for viewer in viewers:
                if type(viewer) == CILViewer2D:
                    viewer.setInputData2(image2)
            self.input_data2 = image2

        
class standalone_viewer(object):
    '''a Qt interactive viewer where the user can set 1 or 2 input datasets'''
    def __init__(self, title= "", viewer1_type='2D', viewer2_type = '3D', *args, **kwargs):
        '''Creator'''
        app = QtWidgets.QApplication(sys.argv)
        self.app = app
        
        self.set_up(title, viewer1_type, viewer2_type, *args, **kwargs)
        self.show()

    def set_up(self, title, viewer1_type, viewer2_type = None, *args, **kwargs):
        '''
        viewer1_type: '2D' or '3D'
        viewer2_type: '2D', '3D' or None - if None, only one viewer is displayed
        '''

        if viewer1_type == '2D':
            viewer1 = viewer2D
        elif viewer1_type == '3D':
            viewer1 = viewer3D

        if viewer2_type is not None:
            if viewer2_type == '2D':
                viewer2 = viewer2D
            elif viewer2_type == '3D':
                viewer2 = viewer3D

        window = StandaloneViewerMainWindow(title, viewer1=viewer1, viewer2=viewer2)

        self.window = window
        self.has_run = None

        window.show()

    def show(self):
        if self.has_run is None:
            self.has_run = self.app.exec_()
        else:
            print ('No instance can be run interactively again. Delete and re-instantiate.')

    def __del__(self):
        '''destructor'''
        self.app.exit()

if __name__ == "__main__":

    err = vtk.vtkFileOutputWindow()
    err.SetFileName("../viewer.log")
    vtk.vtkOutputWindow.SetInstance(err)
    
    #iviewer(reader.GetOutput(), viewer='3D')
    standalone_viewer("Test Standalone Viewer", viewer1_type='2D', viewer2_type='3D')


