import sys

import ccpi.viewer.viewerLinker as vlink
import numpy as np
import vtk
from ccpi.viewer import viewer2D, viewer3D
from ccpi.viewer.QCILViewerWidget import QCILViewerWidget
from ccpi.viewer.utils.conversion import Converter
from PySide2 import QtWidgets


class SingleViewerCenterWidget(QtWidgets.QMainWindow):

    def __init__(self, parent=None, viewer=viewer2D):
        QtWidgets.QMainWindow.__init__(self, parent)

        self.frame = QCILViewerWidget(viewer=viewer, shape=(600, 600))

        self.setCentralWidget(self.frame)

        self.show()

    def set_input(self, data):
        self.frame.viewer.setInputData(data)


class TwoLinkedViewersCenterWidget(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        # self.resize(800,600)

        self.frame1 = QCILViewerWidget(viewer=viewer2D, shape=(600, 600),
                                       interactorStyle=vlink.Linked2DInteractorStyle)
        self.frame2 = QCILViewerWidget(viewer=viewer2D, shape=(600, 600),
                                       interactorStyle=vlink.Linked2DInteractorStyle)

        # Initially link viewers
        self.linkedViewersSetup()
        self.linker.enable()

        layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight)
        layout.addWidget(self.frame1)
        layout.addWidget(self.frame2)

        cw = QtWidgets.QWidget()
        cw.setLayout(layout)
        self.setCentralWidget(cw)
        self.central_widget = cw

        self.show()

    def linkedViewersSetup(self):
        v1 = self.frame1.viewer
        v2 = self.frame2.viewer
        self.linker = vlink.ViewerLinker(v1, v2)
        self.linker.setLinkPan(True)
        self.linker.setLinkZoom(True)
        self.linker.setLinkWindowLevel(True)
        self.linker.setLinkSlice(True)

    def set_input(self, data1, data2):
        self.frame1.viewer.setInputData(data1)
        self.frame2.viewer.setInputData(data2)


class iviewer(object):
    '''a Qt interactive viewer that can be used as plotter2D with one single dataset'''

    def __init__(self, data, *moredata, **kwargs):
        '''Creator'''
        app = QtWidgets.QApplication(sys.argv)
        self.app = app

        self.setUp(data, *moredata, **kwargs)
        self.show()

    def setUp(self, data, *moredata, **kwargs):
        if len(moredata) == 0:
            # can change the behaviour by setting which viewer you want
            # between viewer2D and viewer3D
            viewer_type = kwargs.get('viewer', '2D')
            if viewer_type == '2D':
                viewer = viewer2D
            elif viewer_type == '3D':
                viewer = viewer3D
            window = SingleViewerCenterWidget(viewer=viewer)
            window.set_input(self.convert_to_vtkImage(data))
        else:
            window = TwoLinkedViewersCenterWidget()
            window.set_input(self.convert_to_vtkImage(data),
                             self.convert_to_vtkImage(moredata[0]))
            viewer_type = None

        self.window = window
        self.viewer_type = viewer_type
        self.has_run = None

    def show(self):
        if self.has_run is None:
            self.has_run = self.app.exec_()
        else:
            print(
                'No instance can be run interactively again. Delete and re-instantiate.')

    def __del__(self):
        '''destructor'''
        self.app.exit()

    def convert_to_vtkImage(self, data):
        '''convert the data to vtkImageData for the viewer'''
        if isinstance(data, vtk.vtkImageData):
            vtkImage = data

        elif isinstance(data, np.ndarray):
            vtkImage = Converter.numpy2vtkImage(data)

        elif hasattr(data, 'as_array'):
            # this makes it likely it is a CIL/SIRF DataContainer
            # currently this will only deal with the actual data
            # but it will parse the metadata in future
            return self.convert_to_vtkImage(data.as_array())

        return vtkImage


if __name__ == "__main__":

    err = vtk.vtkFileOutputWindow()
    err.SetFileName("viewer.log")
    vtk.vtkOutputWindow.SetInstance(err)

    reader = vtk.vtkMetaImageReader()
    reader.SetFileName('head.mha')
    reader.Update()

    #iviewer(reader.GetOutput(), viewer='3D')
    iviewer(reader.GetOutput(), reader.GetOutput())
