import vtk
import sys
import vtk
from PySide2 import QtCore, QtWidgets
from ccpi.viewer.QCILRenderWindowInteractor import QCILRenderWindowInteractor
from ccpi.viewer import viewer2D


class QCILViewerWidget(QtWidgets.QFrame):
    '''A QFrame to embed in Qt application containing a VTK Render Window
    
    All the interaction is passed from Qt to VTK.

    :param viewer: The viewer you want to embed in Qt: CILViewer2D or CILViewer
    :param interactorStyle: The interactor style for the Viewer. 
    '''

    def __init__(self, parent, viewer, shape=(600, 600), debug=False, renderer=None, interactorStyle=None):
        '''Creator. Creates an instance of a QFrame and of a CILViewer
        
        The viewer is placed in the QFrame inside a QVBoxLayout. 
        The viewer is accessible as member 'viewer'
        '''

        super(QCILViewerWidget, self).__init__(parent=parent)
        # currently the size of the frame is set by stretching to the whole
        # area in the main window. A resize of the MainWindow triggers a resize of
        # the QFrame to occupy the whole area available.

        dimx, dimy = shape
        # self.resize(dimx, dimy)

        self.vtkWidget = QCILRenderWindowInteractor(self)

        if renderer is None:
            self.ren = vtk.vtkRenderer()
        else:
            self.ren = renderer

        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        # https://discourse.vtk.org/t/qvtkwidget-render-window-is-outside-main-qt-app-window/1539/8?u=edoardo_pasca
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()

        try:
            
            self.viewer = viewer(dimx=dimx,
                                 dimy=dimy,
                                 ren=self.ren,
                                 renWin=self.vtkWidget.GetRenderWindow(),
                                 iren=self.iren,
                                 debug=debug)
        except KeyError:
            raise KeyError("Viewer class not provided. Submit an uninstantiated viewer class object"
                           "using 'viewer' keyword")

        if interactorStyle is not None:
            self.viewer.style = interactorStyle(self.viewer)
            self.viewer.iren.SetInteractorStyle(self.viewer.style)

        self.vl = QtWidgets.QVBoxLayout()
        self.vl.addWidget(self.vtkWidget)
        self.setLayout(self.vl)
        self.adjustSize()


class QCILDockableWidget(QtWidgets.QDockWidget):

    def __init__(self, parent=None, viewer=viewer2D, shape=(600, 600), interactorStyle=None, title=""):

        super(QCILDockableWidget, self).__init__(parent)

        self.frame = QCILViewerWidget(parent, viewer, shape=shape, interactorStyle=interactorStyle)
        self.viewer = self.frame.viewer

        self.setWindowTitle(title)

        self.setWidget(self.frame)
