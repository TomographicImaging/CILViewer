from PySide2 import QtCore, QtWidgets
from ccpi.viewer.QCILRenderWindowInteractor import QCILRenderWindowInteractor
from ccpi.viewer import viewer2D, viewer3D


class QCILViewer3DToolBar(QtWidgets.QToolBar):
    def __init__(self, parent=None, **kwargs):
        super(QCILViewer3DToolBar, self).__init__(parent=parent, **kwargs)
        button1 = QtWidgets.QToolButton()
        button1.setText("1")
        button2 = QtWidgets.QToolButton()
        button2.setText("2")
        self.addWidget(button1)
        self.addWidget(button2)
