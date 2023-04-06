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
from ccpi.viewer.CILViewer2D import CILViewer2D
from ccpi.viewer.CILViewer import CILViewer
from ccpi.viewer.iviewer import SingleViewerCenterWidget
from ccpi.viewer.QCILViewerWidget import QCILDockableWidget, QCILViewerWidget
# from gui.settings_window import create_settings_window
from ccpi.viewer.utils import Converter, cilPlaneClipper
from ccpi.viewer.utils.conversion import Converter, cilNumpyMETAImageWriter
# , QCILViewerWidget
from ccpi.viewer.utils.hdf5_io import HDF5Reader
from ccpi.viewer.utils.io import ImageReader
from ccpi.viewer.viewer_main_window import ViewerMainWindow
from eqt.threading import Worker
from eqt.ui import FormDialog
from eqt.ui.UIFormWidget import UIFormFactory
from eqt.ui.UIStackedWidget import StackedWidgetFactory
# from eqt.ui.UIFormWidget import UIFormFactory
from PySide2 import QtCore, QtWidgets
from PySide2.QtCore import QRegExp, QSettings, Qt, QThreadPool
from PySide2.QtGui import QCloseEvent, QKeySequence, QRegExpValidator
from PySide2.QtWidgets import (QAction, QCheckBox, QComboBox, QDockWidget,
                               QFileDialog, QLabel, QLineEdit, QMainWindow,
                               QMenu, QMessageBox, QProgressDialog,
                               QPushButton, QSpinBox, QStackedWidget,
                               QTabWidget)

#from ccpi.viewer.utils.io import ImageDataCreator




# TODO next - get progress from Worker

# TODO: see line 654 in iDVC to get resample rate from returned image from io
# but we will scrap io!
# instead look at how to get the resample rate of downsampled images

class TwoViewersMainWindow(ViewerMainWindow):
    def __init__(self, title = "StandaloneViewer", app_name = "Standalone Viewer", settings_name=None,
                 organisation_name=None, viewer1=viewer2D, viewer2=viewer3D):
        ViewerMainWindow.__init__(self, title, app_name, settings_name, organisation_name)

        if viewer1 == viewer2D:
            interactor_style1 = vlink.Linked2DInteractorStyle
            dock1_title = "2D View"
        elif viewer1 == viewer3D:
            interactor_style1 = vlink.Linked3DInteractorStyle
            dock1_title = "3D View"

        if viewer2 == viewer2D:
            interactor_style2 = vlink.Linked2DInteractorStyle
            dock2_title = "2D View"
        elif viewer2 == viewer3D:
            interactor_style2 = vlink.Linked3DInteractorStyle
            dock2_title = "3D View"

        dock1 = QCILDockableWidget(viewer=viewer1, shape=(600,600),
              interactorStyle=interactor_style1, title=dock1_title)
        
        dock2 = QCILDockableWidget(viewer=viewer2, shape=(600,600),
              interactorStyle=interactor_style2, title=dock2_title)

        self.frame1 = dock1.frame
        self.frame2 = dock2.frame
        self.viewer1 = self.frame1.viewer
        self.viewer2 = self.frame2.viewer

        self.viewers = [self.viewer1, self.viewer2]

        self.viewer_coords_dock.setViewers(self.viewers)
                
        # Initially link viewers
        self.linkedViewersSetUp()
        self.linker.enable()
        
        cw = QMainWindow()
        cw.addDockWidget(Qt.LeftDockWidgetArea, dock1)
        cw.addDockWidget(Qt.RightDockWidgetArea, dock2)
        self.setCentralWidget(cw)
        self.central_widget = cw

    
    def linkedViewersSetUp(self):
        v1 = self.frame1.viewer
        v2 = self.frame2.viewer
        self.linker = vlink.ViewerLinker(v1, v2)
        self.linker.setLinkPan(True)
        self.linker.setLinkZoom(True)
        self.linker.setLinkWindowLevel(True)
        self.linker.setLinkSlice(True)    

    def setAppSettingsDialogWidgets(self, dialog):
        '''Override the method to remove Copy Files checkbox from the dialog'''
        super().setAppSettingsDialogWidgets(dialog)

        widget_to_remove = dialog.getWidget('copy_files_checkbox_field')
        layout = dialog.formWidget.getLayout()
        layout.removeWidget(widget_to_remove)
        dialog.formWidget.widgets.pop('copy_files_checkbox_field')

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



class StandaloneViewerMainWindow(TwoViewersMainWindow):
    def __init__(self, title = "StandaloneViewer", app_name = "Standalone Viewer", settings_name=None,
                 organisation_name=None, viewer1=viewer2D, viewer2=viewer3D):
        TwoViewersMainWindow.__init__(self, title, app_name, settings_name, organisation_name)

        self.image_overlay = vtk.vtkImageData()


    def addToMenu(self):
        '''
        Adds actions to the menu bar for selecting the images to be displayed
        '''
        file_menu = self.menus['File']

        # Find the Save session actions and remove them from the menu      
        for action in file_menu.actions():
            action_name = action.text()
            if action_name == 'Save' or action_name == 'Save + Exit':
                file_menu.removeAction(action)
            
        # insert image selection as first action in file menu:

        image2_action = QAction("Select Image Overlay", self)
        image2_action.triggered.connect(lambda: self.setViewersInput([self.viewer1], input_num=2))
        file_menu.insertAction(file_menu.actions()[0], image2_action)

        image1_action = QAction("Select Image", self)
        image1_action.triggered.connect(lambda: self.setViewersInput([self.viewer1, self.viewer2]))
        file_menu.insertAction(file_menu.actions()[0], image1_action)

    def closeEvent(self, event):
        '''
        Overwrites the SessionMainWindow's closeEvent 
        so that the application is closed when the window is closed.

        This method occurs when we call self.close() or when the user clicks the X button on the window.
        '''
        pass

    def createViewerCoordsDockWidget(self):
        '''
        Creates a dock widget which contains widgets for displaying the 
        image shown on the viewer, and the coordinate system of the viewer.

        Override to add checkbox for showing and hiding the image overlay.
        '''
        super().createViewerCoordsDockWidget()
        checkbox = QCheckBox("Show Image Overlay")
        checkbox.setChecked(True)
        checkbox.setVisible(False)
        self.viewer_coords_dock.widget().addSpanningWidget(checkbox, 'image_overlay')
        checkbox.stateChanged.connect(partial(self.showHideImageOverlay, self.viewer_coords_dock.viewers))

    def showHideImageOverlay(self, viewers, state):
        '''
        Shows or hides the image overlay on the viewers
        '''
        for viewer in viewers:
            if isinstance(viewer, viewer2D):
                if state:
                    viewer.setInputData2(self.image_overlay)
                else:
                    self.image_overlay = viewer.image2
                    viewer.setInputData2(vtk.vtkImageData())

        
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


