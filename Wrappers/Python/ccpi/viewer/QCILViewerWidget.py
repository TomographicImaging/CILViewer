import vtk
import sys
import vtk
from PySide2 import QtCore, QtWidgets
from ccpi.viewer.QCILRenderWindowInteractor import QCILRenderWindowInteractor
from ccpi.viewer import viewer2D, viewer3D
from ccpi.viewer.QCILViewer3DToolBar import QCILViewer3DToolBar


class QCILViewerWidget(QtWidgets.QFrame):
    '''A QFrame to embed in Qt application containing a VTK Render Window
    
    All the interaction is passed from Qt to VTK.

    :param viewer: The viewer you want to embed in Qt: CILViewer2D or CILViewer
    :param interactorStyle: The interactor style for the Viewer. 
    '''

    def __init__(self,
                 parent,
                 viewer,
                 shape=(600, 600),
                 debug=False,
                 renderer=None,
                 interactorStyle=None,
                 enableSliderWidget=True):
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

        if viewer is viewer2D:
            self.viewer = viewer(dimx=dimx,
                                 dimy=dimy,
                                 ren=self.ren,
                                 renWin=self.vtkWidget.GetRenderWindow(),
                                 iren=self.iren,
                                 debug=debug,
                                 enableSliderWidget=enableSliderWidget)
            al = self.viewer.axisLabelsText
            self.viewer.setAxisLabels([al[0], al[1], ''], False)
        elif viewer is viewer3D:
            self.viewer = viewer(dimx=dimx,
                                 dimy=dimy,
                                 ren=self.ren,
                                 renWin=self.vtkWidget.GetRenderWindow(),
                                 iren=self.iren,
                                 debug=debug)
        else:
            raise KeyError("Viewer class not provided. Submit an uninstantiated viewer class object"
                           "using 'viewer' keyword")

        if interactorStyle is not None:
            self.viewer.style = interactorStyle(self.viewer)
            self.viewer.iren.SetInteractorStyle(self.viewer.style)

        self.vl = QtWidgets.QVBoxLayout()

        self._toolBar = None
        toolBar = self.getToolbar(parent)
        if toolBar is not None:
            self.vl.addWidget(toolBar)

        self.vl.addWidget(self.vtkWidget)

        self.setLayout(self.vl)
        self.adjustSize()

    def getToolbar(self, parent=None):
        if self._toolBar is not None:
            return self._toolBar
        # Adds a toolbar to the QFrame if we have a 3D viewer
        if isinstance(self.viewer, viewer3D):
            toolBar = QCILViewer3DToolBar(viewer=self.viewer, parent=parent)
            self._toolBar = toolBar
            return toolBar


class QCILDockableWidget(QtWidgets.QDockWidget):
    '''Inserts a vtk viewer in a dock widget.'''

    def __init__(self, parent=None, viewer=viewer2D, shape=(600, 600), interactorStyle=None, title=""):
        '''Creates an instance of a `QCILDockableWidget` and inserts it in a `QDockWidget`. 
        Sets the title of the dock widget.'''
        super(QCILDockableWidget, self).__init__(parent)

        self.frame = QCILViewerWidget(parent, viewer, shape=shape, interactorStyle=interactorStyle)
        self.viewer = self.frame.viewer

        self.setWindowTitle(title)

        self.setWidget(self.frame)
