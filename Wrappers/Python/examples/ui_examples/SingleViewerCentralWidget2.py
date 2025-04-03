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
        x,y = 450, 250
        dx, dy = 1000, 1000
        self.setGeometry(x,y, x+dx , y+dy)
        self.frame = QCILViewerWidget(parent, viewer=viewer, shape=(dx, dy), debug=True)

        head = example_data.HEAD.get()
        
        self.frame.viewer.setInputData2(head)

        self.setCentralWidget(self.frame)

        self.show()


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    # can change the behaviour by setting which viewer you want
    # between viewer2D and viewer3D
    window = SingleViewerCenterWidget(viewer=viewer2D)

    sys.exit(app.exec_())
