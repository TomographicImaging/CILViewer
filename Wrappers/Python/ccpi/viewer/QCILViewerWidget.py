
from PyQt5 import QtWidgets
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

class QVTKWidget(QtWidgets.QFrame):
    '''A QFrame to embed in Qt application containing a VTK Render Window
    
    All the interaction is passed from Qt to VTK.

    :param viewer: The viewer you want to embed in Qt: CILViewer2D or CILViewer
    :param interactorStyle: The interactor style for the Viewer. 
    '''
    def __init__(self, viewer, **kwargs):
        '''Creator. Creates an instance of a QFrame and of a CILViewer
        
        The viewer is placed in the QFrame inside a QVBoxLayout. 
        The viewer is accessible as member 'viewer'
        '''
        super(QtWidgets.QFrame, self).__init__()
        self.vl = QtWidgets.QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.vl.addWidget(self.vtkWidget)
 
        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.viewer = viewer(renWin = self.vtkWidget.GetRenderWindow(),
                                iren = self.iren, 
                                ren = self.ren)
        # except KeyError:
        #     raise KeyError("Viewer class not provided. Submit an uninstantiated viewer class object"
        #                    "using 'viewer' keyword")
        
        

        if 'interactorStyle' in kwargs.keys():
            self.viewer.style = kwargs['interactorStyle'](self.viewer)
            self.viewer.iren.SetInteractorStyle(self.viewer.style)
        
        self.setLayout(self.vl)
    