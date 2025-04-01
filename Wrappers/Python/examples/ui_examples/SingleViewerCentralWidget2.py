import sys
import vtk
from qtpy import QtCore, QtWidgets
from ccpi.viewer import viewer2D, viewer3D
from ccpi.viewer.QCILViewerWidget import QCILViewerWidget
import os
from ccpi.viewer.utils import example_data


class SingleViewerCenterWidget(QtWidgets.QMainWindow):

    def __init__(self, parent=None, viewer=viewer2D):
        QtWidgets.QMainWindow.__init__(self, parent)
        x,y = 0, 0
        dx, dy = 500, 500
        self.setGeometry(x,y, x+dx , y+dy)
        self.frame = QCILViewerWidget(parent, viewer=viewer, shape=(dx, dy), debug=True)

        # head = example_data.HEAD.get()
        from ccpi.viewer.utils.conversion import Converter
        import numpy as np

        ndata = np.load("/Users/edoardo.pasca/Data/DVC_test_images/frame_010_f.npy")
        data = Converter.numpy2vtkImage(ndata)

        self.frame.viewer.setInputData(data)
        # self.frame.viewer.setInputData2(head)

        self.setCentralWidget(self.frame)

        self.show()


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    # can change the behaviour by setting which viewer you want
    # between viewer2D and viewer3D
    window = SingleViewerCenterWidget(viewer=viewer2D)

    sys.exit(app.exec_())
