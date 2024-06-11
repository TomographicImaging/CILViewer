import sys
from functools import partial

import vtk
from ccpi.viewer import viewer2D, viewer3D
from ccpi.viewer.ui.main_windows import TwoViewersMainWindow
from PySide2 import QtWidgets
from PySide2.QtWidgets import QAction, QCheckBox
import logging
import argparse


class StandaloneViewerMainWindow(TwoViewersMainWindow):
    '''
    A main window for displaying two viewers side by side, with a menu bar
    for selecting the images to be displayed.

    The first image selected will be displayed on both viewers. The second
    is an image overlay which is displayed on the 2D viewer/s only.

    A dock widget is created which contains widgets for displaying the
    file name of the image shown on the viewer, and the level of downsampling
    of the image displayed on the viewer.    
    '''

    def __init__(self,
                 title="StandaloneViewer",
                 app_name="Standalone Viewer",
                 settings_name=None,
                 organisation_name=None,
                 viewer1_type='2D',
                 viewer2_type='3D',
                 scale_factor=1,
                 max_opacity=0.1):
        super(StandaloneViewerMainWindow, self).__init__(title, app_name, settings_name, organisation_name,
                                                         viewer1_type, viewer2_type)

        self.addToMenu()
        self.addToViewerCoordsDockWidget()

        self.image_overlay = vtk.vtkImageData()

        # apply scale factor to sliders in the viewer3D dock widget:
        logging.debug("scale_factor = {}".format(scale_factor))
        self.scale_factor = scale_factor
        self.frames[1].getToolbar().scale_factor = scale_factor
        logging.debug(f"Setting maximum opacity for volume render to: {max_opacity}")
        self.frames[1].viewer.setMaximumOpacity(max_opacity)

    def addToMenu(self):
        '''
        Adds actions to the menu bar for selecting the images to be displayed
        '''
        file_menu = self.menus['File']

        # insert image selection as first action in file menu:

        image2_action = QAction("Select Image Overlay", self)
        image2_action.triggered.connect(lambda: self.setViewersInputFromDialog(self.viewers, input_num=2))
        file_menu.insertAction(file_menu.actions()[0], image2_action)

        image1_action = QAction("Select Image", self)
        image1_action.triggered.connect(lambda: self.setViewersInputFromDialog(self.viewers))
        file_menu.insertAction(file_menu.actions()[0], image1_action)

    def addToViewerCoordsDockWidget(self):
        '''
        Adds widgets to the viewer coords dock widget for displaying the
        image overlay, and for showing/hiding the 2D and 3D viewers.
        '''
        checkbox = QCheckBox("Show Image Overlay")
        checkbox.setChecked(True)
        self.viewer_coords_dock.widget().addSpanningWidget(checkbox, 'image_overlay')
        checkbox.stateChanged.connect(partial(self.showHideImageOverlay))

        checkbox2 = QCheckBox("Show 2D Viewer")
        checkbox2.setChecked(True)
        checkbox2.stateChanged.connect(partial(self.showHideViewer, 0))

        checkbox3 = QCheckBox("Show 3D Viewer")
        checkbox3.setChecked(True)
        self.viewer_coords_dock.widget().addWidget(checkbox3, checkbox2, 'show_viewer')
        checkbox3.stateChanged.connect(partial(self.showHideViewer, 1))

    def showHideImageOverlay(self, show=True):
        '''
        Shows or hides the image overlay/s on the viewers
        '''
        for viewer in self.viewer_coords_dock.viewers:
            if isinstance(viewer, viewer2D):
                if show:
                    if hasattr(self, 'image_overlay'):
                        viewer.setInputData2(self.image_overlay)
                else:
                    self.image_overlay = viewer.image2
                    viewer.setInputData2(vtk.vtkImageData())


class standalone_viewer(object):
    '''
    Launches a StandaloneViewerMainWindow instance.

    Parameters:
    ------------
    title: str
        title of the window
    viewer1_type: '2D' or '3D'
    viewer2_type: '2D', '3D' or None 
        if None, only one viewer is displayed
    '''

    def __init__(self, title="", viewer1_type='2D', viewer2_type='3D', *args, **kwargs):
        '''Creator
        
        Parameters:
        ------------
        title: str
            title of the window
        viewer1_type: '2D' or '3D'
        viewer2_type: '2D', '3D' or None 
            if None, only one viewer is displayed
        '''
        app = QtWidgets.QApplication(sys.argv)
        self.app = app

        self.set_up(title, viewer1_type, viewer2_type, *args, **kwargs)

    def set_up(self, title, viewer1_type, viewer2_type=None, *args, **kwargs):
        '''
        Sets up the standalone viewer.

        Parameters:
        ------------
        title: str
            title of the window
        viewer1_type: '2D' or '3D'
        viewer2_type: '2D', '3D' or None 
            if None, only one viewer is displayed
        '''

        window = StandaloneViewerMainWindow(title, viewer1_type, viewer2_type, *args, **kwargs)

        self.window = window
        self.has_run = None

        window.show()

    def show(self):
        '''
        Shows the window
        '''
        if self.has_run is None:
            self.has_run = self.app.exec_()
        else:
            print('No instance can be run interactively again. Delete and re-instantiate.')

    def __del__(self):
        '''destructor'''
        self.app.exit()


def main():

    parser = argparse.ArgumentParser(description='Standalone CIL Viewer')

    parser.add_argument('--debug', type=str)
    parser.add_argument('--scale_factor', type=float, default=1)
    parser.add_argument('--max_opacity', type=float, default=0.1)
    args = parser.parse_args()

    if args.debug in ['debug', 'info', 'warning', 'error', 'critical']:
        level = eval(f'logging.{args.debug.upper()}')
        logging.basicConfig(level=level)
        logging.info(f"cilviewer: Setting debugging level to {args.debug.upper()}")

    logging.debug(f"scale_factor: {args.scale_factor}")
    logging.debug(f"max_opacity: {args.max_opacity}")

    # Run a standalone viewer with a 2D and a 3D viewer:
    err = vtk.vtkFileOutputWindow()
    err.SetFileName("viewer.log")
    vtk.vtkOutputWindow.SetInstance(err)
    standalone_viewer_instance = standalone_viewer("Standalone Viewer",
                                                   viewer1_type='2D',
                                                   viewer2_type='3D',
                                                   scale_factor=args.scale_factor,
                                                   max_opacity=args.max_opacity)
    standalone_viewer_instance.show()
    return 0


if __name__ == '__main__':
    main()
