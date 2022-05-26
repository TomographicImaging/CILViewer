import sys
import vtk
from PySide2 import QtCore, QtWidgets
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from ccpi.viewer.QCILRenderWindowInteractor import QCILRenderWindowInteractor
from ccpi.viewer import viewer2D, viewer3D
from ccpi.viewer.QCILViewerWidget import QCILViewerWidget
# Import linking class to join 2D and 3D viewers
import ccpi.viewer.viewerLinker as vlink


class SingleViewerCenterWidget(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        #self.resize(800,600)

        self.frame = QCILViewerWidget(viewer=viewer3D, shape=(600, 600))

        reader = vtk.vtkMetaImageReader()
        reader.SetFileName('head.mha')
        reader.Update()

        self.frame.viewer.setInputData(reader.GetOutput())

        self.setCentralWidget(self.frame)

        self.show()


class TwoLinkedViewersCenterWidget(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        #self.resize(800,600)

        self.frame1 = QCILViewerWidget(
            viewer=viewer2D,
            shape=(600, 600),
            interactorStyle=vlink.Linked2DInteractorStyle)
        self.frame2 = QCILViewerWidget(
            viewer=viewer3D,
            shape=(600, 600),
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


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    #window = MainWindow3()
    window = TwoLinkedViewersCenterWidget()

    sys.exit(app.exec_())
