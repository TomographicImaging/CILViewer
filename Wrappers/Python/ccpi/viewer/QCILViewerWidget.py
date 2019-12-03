
from PyQt5 import QtWidgets
import vtk
import sys
import vtk
from PyQt5 import QtCore, QtWidgets
from ccpi.viewer.QCILRenderWindowInteractor import QCILRenderWindowInteractor
from ccpi.viewer import viewer2D

class QCILViewerWidget(QtWidgets.QFrame):
    '''A QFrame to embed in Qt application containing a VTK Render Window
    
    All the interaction is passed from Qt to VTK.

    :param viewer: The viewer you want to embed in Qt: CILViewer2D or CILViewer
    :param interactorStyle: The interactor style for the Viewer. 
    '''
    def __init__(self, parent=None, **kwargs):
        '''Creator. Creates an instance of a QFrame and of a CILViewer
        
        The viewer is placed in the QFrame inside a QVBoxLayout. 
        The viewer is accessible as member 'viewer'
        '''
        
        super(QtWidgets.QFrame, self).__init__()
        # currently the size of the frame is set by stretching to the whole 
        # area in the main window. A resize of the MainWindow triggers a resize of 
        # the QFrame to occupy the whole area available.

        dimx, dimy = kwargs.get('shape', (600,600))
        # self.resize(dimx, dimy)

        self.vl = QtWidgets.QVBoxLayout()
        #self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.vtkWidget = QCILRenderWindowInteractor(self)
        self.vl.addWidget(self.vtkWidget)
        
        if 'renderer' in kwargs.keys():
            self.ren = kwargs['renderer']
        else:
            self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        try:
            
            print ("provided viewer class ", kwargs['viewer'])
            self.viewer = kwargs['viewer'](renWin = self.vtkWidget.GetRenderWindow(),
                                           iren = self.iren, 
                                           ren = self.ren,
                                           dimx=dimx,
                                           dimy=dimy,
                                           debug=kwargs.get('debug', False)
                                           )
        except KeyError:
            raise KeyError("Viewer class not provided. Submit an uninstantiated viewer class object"
                           "using 'viewer' keyword")
        
        

        if 'interactorStyle' in kwargs.keys():
            self.viewer.style = kwargs['interactorStyle'](self.viewer)
            self.viewer.iren.SetInteractorStyle(self.viewer.style)
        
        self.setLayout(self.vl)
        self.adjustSize()

class QCILDockableWidget(QtWidgets.QDockWidget):

    def __init__(self, parent=None, **kwargs):
        viewer = kwargs.get('viewer', viewer2D)
        shape = kwargs.get('shape', (600,600))
        title = kwargs.get('title', "3D View")


        super(QCILDockableWidget, self).__init__(parent)
        
        

        self.frame = QCILViewerWidget(parent, **kwargs)
        self.viewer = self.frame.viewer

        self.setWindowTitle(title)
        
        self.setWidget(self.frame)