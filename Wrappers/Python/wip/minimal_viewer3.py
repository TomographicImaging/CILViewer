import sys
import vtk
from PyQt5 import QtCore, QtWidgets
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from ccpi.viewer.QCILRenderWindowInteractor import QCILRenderWindowInteractor
from ccpi.viewer import viewer2D, viewer3D
from ccpi.viewer.QCILViewerWidget import QCILViewerWidget, QCILDockableWidget
# Import linking class to join 2D and 3D viewers
import ccpi.viewer.viewerLinker as vlink
from ccpi.viewer.utils import colormaps
from qrangeslider import QRangeSlider
import numpy


class SingleViewerCenterWidget(QtWidgets.QMainWindow):

    def __init__(self, parent = None):
        QtWidgets.QMainWindow.__init__(self, parent)
        #self.resize(800,600)
        
        self.frame = QCILViewerWidget(viewer=viewer3D, shape=(600,600))
                
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName('head.mha')
        reader.Update()
        
        self.frame.viewer.setInputData(reader.GetOutput())
        
        self.setCentralWidget(self.frame)
    
        self.show()
        
class TwoLinkedViewersCenterWidget(QtWidgets.QMainWindow):

    def __init__(self, parent = None):
        QtWidgets.QMainWindow.__init__(self, parent)
        #self.resize(800,600)
        
        self.frame1 = QCILViewerWidget(viewer=viewer2D, shape=(600,600),
              interactorStyle=vlink.Linked2DInteractorStyle)
        self.frame2 = QCILViewerWidget(viewer=viewer3D, shape=(600,600),
              interactorStyle=vlink.Linked3DInteractorStyle)
                
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName('head.mha')
        reader.Update()
        
        self.frame1.viewer.setInputData(reader.GetOutput())
        self.frame2.viewer.setInputData(reader.GetOutput())
        
        # Initially link viewers
        self.linkedViewersSetup()
        self.link2D3D.enable()

        layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight)
        layout.addWidget(self.frame1)
        layout.addWidget(self.frame2)
        
        cw = QtWidgets.QWidget()
        cw.setLayout(layout)
        self.setCentralWidget(cw)
        self.central_widget = cw
        self.show()

    def linkedViewersSetup(self):
        v2d = self.frame1.viewer
        v3d = self.frame2.viewer
        self.link2D3D = vlink.ViewerLinker(v2d, v3d)
        self.link2D3D.setLinkPan(False)
        self.link2D3D.setLinkZoom(False)
        self.link2D3D.setLinkWindowLevel(True)
        self.link2D3D.setLinkSlice(True)


class SingleViewerDockableWidget(QtWidgets.QMainWindow):

    def __init__(self, parent = None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.resize(800,600)
        
        self.Dock3D = QtWidgets.QDockWidget(parent=self)
        
        self.frame = QCILViewerWidget(viewer=viewer3D, shape=(800,600))

        # self.Dock3D.setMinimumWidth(300)
        self.Dock3D.setWindowTitle("3D View")

        self.Dock3D.setWidget(self.frame)
        

        reader = vtk.vtkMetaImageReader()
        reader.SetFileName('head.mha')
        reader.Update()
        
        self.frame.viewer.setInputData(reader.GetOutput())
        
        # self.setCentralWidget(self.frame)
    
        

        # self.Dock3DContents = QtWidgets.QWidget()
        # self.Dock3DContents.setStyleSheet("background-color: rgb(25,51,101)")
        # f_layout3D = Qt.QFormLayout(self.Dock3DContents)

        
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.Dock3D)

        self.show()

class SingleViewerDockableWidget2(QtWidgets.QMainWindow):

    def __init__(self, parent = None):
        QtWidgets.QMainWindow.__init__(self, parent)
        #self.resize(800,600)
        
        self.frame = QCILDockableWidget(viewer=viewer2D, shape=(600,600), title="Test 2D")
                
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName('head.mha')
        reader.Update()
        
        self.frame.viewer.setInputData(reader.GetOutput())
        
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.frame)

        self.show()

class FourLinkedViewersDockableWidget(QtWidgets.QMainWindow):

    def __init__(self, parent = None):
        QtWidgets.QMainWindow.__init__(self, parent)
        #self.resize(800,600)
        
        # create the dockable widgets with the viewer inside
        self.v00 = QCILDockableWidget(viewer=viewer2D, shape=(600,600), 
           title="X", interactorStyle=vlink.Linked2DInteractorStyle, debug=False)
        self.v01 = QCILDockableWidget(viewer=viewer2D, shape=(600,600), 
           title="Y", interactorStyle=vlink.Linked2DInteractorStyle, debug=False)
        self.v10 = QCILDockableWidget(viewer=viewer2D, shape=(600,600), 
           title="Z", interactorStyle=vlink.Linked2DInteractorStyle, debug=False)
        self.v11 = QCILDockableWidget(viewer=viewer3D, shape=(600,600), 
           title="3D", interactorStyle=vlink.Linked3DInteractorStyle, debug=True)
                
        # Create the viewer linkers 
        viewerLinkers = self.linkedViewersSetup(self.v00, self.v01, self.v10)
        
        for linker in viewerLinkers:
            linker.enable()

        self.viewerLinkers = viewerLinkers

        reader = vtk.vtkMetaImageReader()
        reader.SetFileName('head.mha')
        reader.Update()
        
        for el in [self.v00, self.v01, self.v10, self.v11]:
            el.viewer.setInputData(reader.GetOutput())
        # set slice orientation
        self.v00.viewer.setSliceOrientation('x')
        self.v01.viewer.setSliceOrientation('y')
        self.v10.viewer.setSliceOrientation('z')
        
        # add to the GUI

        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.v00, QtCore.Qt.Vertical)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.v01, QtCore.Qt.Vertical)
        
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.v10, QtCore.Qt.Vertical)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.v11, QtCore.Qt.Vertical)

        # self.rs = QRangeSlider()

        # cmin = self.v00.viewer.ia.GetMinimum()
        # cmax = self.v00.viewer.ia.GetMaximum()
        # self.rs.setRange(cmin,cmax)
        # self.rs.setMin(cmin)
        # self.rs.setMax(cmax)

        # self.rs.endValueChanged.connect(self.updateVolumeRender)
        # self.rs.startValueChanged.connect(self.updateVolumeRender)

        # self.v11.frame.vl.addWidget(self.rs)

        self.show()

    def updateVolumeRender(self):

        self.v11.viewer.updateHistogramPlot()
        self.v11.viewer.setVolumeColorLevelWindow(*self.rs.getRange())
        # self.v11.viewer.linePlotActor.VisibilityOff()

    def linkedViewersSetup(self, *args):
        linked = [viewer for viewer in args]
        # link pair-wise
        pairs = [(linked[i+1],linked[i]) for i in range(len(linked)-1)]
        linkers = []
        for pair in pairs:
            v2d = pair[0].viewer
            v3d = pair[1].viewer
            link2D3D = vlink.ViewerLinker(v2d, v3d)
            link2D3D.setLinkPan(False)
            link2D3D.setLinkZoom(False)
            link2D3D.setLinkWindowLevel(True)
            link2D3D.setLinkSlice(False)
            linkers.append(link2D3D)
        return linkers

def gaussian(x, sigma, b):
    return numpy.exp(-(x-b)**2/(2*sigma**2))

def logistic(x, L, k, x0):
    return L / (1+numpy.exp(-k*(x-x0)))

if __name__ == "__main__":
 
    app = QtWidgets.QApplication(sys.argv)
 
    window = FourLinkedViewersDockableWidget()
    #window = SingleViewerDockableWidget2()
    
    sys.exit(app.exec_())
    