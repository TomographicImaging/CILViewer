import sys
import vtk
from PyQt5 import QtCore, QtWidgets
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from ccpi.viewer.QCILRenderWindowInteractor import QCILRenderWindowInteractor
from ccpi.viewer.CILViewer2D import CILViewer2D
from ccpi.viewer.CILViewer import CILViewer
from ccpi.viewer.QCILViewerWidget import QCILViewerWidget

# class QVTKWidget2(QtWidgets.QFrame):
#     def __init__(self, parent=None, **kwargs):
#         super(QtWidgets.QFrame, self).__init__()
#         self.vl = QtWidgets.QVBoxLayout()
#         #self.vtkWidget = QVTKRenderWindowInteractor(self)
#         self.vtkWidget = QCILRenderWindowInteractor(self)
#         self.vl.addWidget(self.vtkWidget)
 
#         if 'renderer' in kwargs.keys():
#             self.ren = kwargs['renderer']
#         else:
#             self.ren = vtk.vtkRenderer()
#         self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
#         self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
#         try:
#             dimx, dimy = kwargs.get('shape', (600,600))
#             self.viewer = kwargs['viewer'](renWin = self.vtkWidget.GetRenderWindow(),
#                                            iren = self.iren, 
#                                            ren = self.ren,
#                                            dimx=dimx,
#                                            dimy=dimy)
#         except KeyError:
#             raise KeyError("Viewer class not provided. Submit an uninstantiated viewer class object"
#                            "using 'viewer' keyword")
        
        

#         if 'interactorStyle' in kwargs.keys():
#             self.viewer.style = kwargs['interactorStyle'](self.viewer)
#             self.viewer.iren.SetInteractorStyle(self.viewer.style)
        
#         self.setLayout(self.vl)
#         self.adjustSize()

# class MainWindow2(QtWidgets.QMainWindow):
 
#     def __init__(self, parent = None):
#         QtWidgets.QMainWindow.__init__(self, parent)
 
#         self.frame = QVTKWidget2(viewer=CILViewer2D, size=(800,400))
        
        
#         reader = vtk.vtkMetaImageReader()
#         reader.SetFileName('head.mha')
#         reader.Update()
        
#         self.frame.viewer.setInputData(reader.GetOutput())
        
#         self.setCentralWidget(self.frame)
 
#         self.show()
#         # self.iren.Initialize()

class MainWindow3(QtWidgets.QMainWindow):

    def __init__(self, parent = None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.resize(800,600)
        
        self.frame = QCILViewerWidget(viewer=CILViewer, shape=(600,600))
                
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName('head.mha')
        reader.Update()
        
        self.frame.viewer.setInputData(reader.GetOutput())
        
        self.setCentralWidget(self.frame)
    
        self.show()
        
# class MainWindow(QtWidgets.QMainWindow):

#     def __init__(self, parent = None):
#         QtWidgets.QMainWindow.__init__(self, parent)
    
#         self.frame = QtWidgets.QFrame()
    
#         self.vl = QtWidgets.QVBoxLayout()
#         # if one wants to pass a renderer he/she has to define it here
#         self.ren = vtk.vtkRenderer()
#         self.vtkWidget = QVTKRenderWindowInteractor(self.frame, renderer=self.ren)
#         # otherwise it's created by the QVTKRenderWindowInteractor
#         # self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
#         # access the renderer in the QVTKRenderWindowInteractor
#         # self.ren = self.vtkWidget.ren
#         self.vl.addWidget(self.vtkWidget)
        
#         self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()

#         viewer = CILViewer2D(ren = self.ren, renWin = self.vtkWidget.GetRenderWindow(), iren = self.iren)
#         self.viewer = viewer
        
#         reader = vtk.vtkMetaImageReader()
#         reader.SetFileName('head.mha')
#         reader.Update()
#         viewer.setInputData(reader.GetOutput())
#         # # Create source
#         # source = vtk.vtkSphereSource()
#         # source.SetCenter(0, 0, 0)
#         # source.SetRadius(5.0)
    
#         # # Create a mapper
#         # mapper = vtk.vtkPolyDataMapper()
#         # mapper.SetInputConnection(source.GetOutputPort())
    
#         # # Create an actor
#         # actor = vtk.vtkActor()
#         # actor.SetMapper(mapper)
    
#         # self.ren.AddActor(actor)
    
#         # self.ren.ResetCamera()
    
#         self.frame.setLayout(self.vl)
#         self.setCentralWidget(self.frame)
    
#         self.show()
#         # self.iren.Initialize()

if __name__ == "__main__":
 
    app = QtWidgets.QApplication(sys.argv)
 
    window = MainWindow3()
 
    sys.exit(app.exec_())