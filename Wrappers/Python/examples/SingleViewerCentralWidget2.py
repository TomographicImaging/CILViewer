import sys
import vtk
from PySide2 import QtCore, QtWidgets
from ccpi.viewer import viewer2D, viewer3D
from ccpi.viewer.QCILViewerWidget import QCILViewerWidget
import os


class SingleViewerCenterWidget(QtWidgets.QMainWindow):

    def __init__(self, parent=None, viewer=viewer2D):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setGeometry(450, 250, 1000, 1000)
        self.frame = QCILViewerWidget(viewer=viewer, shape=(2000, 2000))

        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(os.path.join("c:/Users/ofn77899/Dev/CILViewer/Wrappers/Python/examples", 'head.mha'))
        reader.Update()
        reader2 = vtk.vtkMetaImageReader()
        reader2.SetFileName(os.path.join("c:/Users/ofn77899/Dev/CILViewer/Wrappers/Python/examples", 'head_root.mha'))
        reader2.Update()
        self.frame.viewer.setInputData(reader2.GetOutput())
        self.frame.viewer.setInputData2(reader.GetOutput())

        self.setCentralWidget(self.frame)

        self.show()


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    # can change the behaviour by setting which viewer you want
    # between viewer2D and viewer3D
    window = SingleViewerCenterWidget(viewer=viewer2D)

    sys.exit(app.exec_())
