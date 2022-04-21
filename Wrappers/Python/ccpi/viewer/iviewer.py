import sys
import vtk
from PySide2 import QtCore, QtWidgets
from ccpi.viewer import viewer2D, viewer3D
from ccpi.viewer.QCILViewerWidget import QCILViewerWidget
import ccpi.viewer.viewerLinker as vlink
from ccpi.viewer.utils.conversion import Converter
import numpy as np

class SingleViewerCenterWidget(QtWidgets.QMainWindow):

    def __init__(self, parent = None, viewer=viewer2D):
        QtWidgets.QMainWindow.__init__(self, parent)
        
        self.frame = QCILViewerWidget(viewer=viewer, shape=(600,600))

        # if viewer == viewer3D:
        #     self.frame.viewer.setVolumeRenderOpacityMethod('scalar')
                
        self.setCentralWidget(self.frame)
    
        self.show()

    def set_input(self, data):
        self.frame.viewer.setInputData(data)
        
class TwoLinkedViewersCenterWidget(QtWidgets.QMainWindow):

    def __init__(self, parent = None, viewer1='2D', viewer2='2D'):
        QtWidgets.QMainWindow.__init__(self, parent)
        #self.resize(800,600)
        styles = []
        viewers = []

        for viewer in [viewer1, viewer2]:
            if viewer == '2D':
                styles.append(vlink.Linked2DInteractorStyle)
            elif viewer == '3D':
                styles.append(vlink.Linked3DInteractorStyle)
            viewers.append(eval('viewer' + viewer))        
        self.frame1 = QCILViewerWidget(viewer=viewers[0], shape=(600,600),
              interactorStyle=styles[0])
        self.frame2 = QCILViewerWidget(viewer=viewers[1], shape=(600,600),
              interactorStyle=styles[1])

        # For the head example we have to set the method to scalar so that
        # the volume render can be seen
        # may need to comment this out for other datasets
        # if viewers[1] == viewer3D:
        #     self.frame2.viewer.setVolumeRenderOpacityMethod('scalar')
                
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
    '''
    a Qt interactive viewer that can be used as plotter2D with one single dataset
    Parameters
    ----------
    data: vtkImageData
        image to be displayed
    moredata: vtkImageData, optional
        extra image to be displayed
    viewer1: string - '2D' or '3D'
        the type of viewer to display the first image on
    viewer2: string - '2D' or '3D', optional
        the type of viewer to display the second image on (if present)
        
    '''
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
            viewer_type = kwargs.get('viewer1', '2D')
            if viewer_type == '2D':
                viewer = viewer2D
            elif viewer_type == '3D':
                viewer = viewer3D
            window = SingleViewerCenterWidget(viewer=viewer)        
            window.set_input(self.convert_to_vtkImage(data))
        else:
            viewer1 = kwargs.get('viewer1', '2D')
            viewer2 = kwargs.get('viewer2', '2D')
            window = TwoLinkedViewersCenterWidget(viewer1=viewer1, viewer2=viewer2)
            window.set_input(self.convert_to_vtkImage(data),
                             self.convert_to_vtkImage(moredata[0]))
            viewer_type = None
            self.viewer1_type = viewer1
            self.viewer2_type = viewer2

        self.window = window
        self.viewer_type = viewer_type
        self.has_run = None

    def show(self):
        if self.has_run is None:
            self.has_run = self.app.exec_()
        else:
            print ('No instance can be run interactively again. Delete and re-instantiate.')

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

    iviewer(reader.GetOutput(), reader.GetOutput(), viewer1='2D', viewer2='3D')
