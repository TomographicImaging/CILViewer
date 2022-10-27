from PySide2 import QtCore, QtWidgets
from ccpi.viewer.QCILRenderWindowInteractor import QCILRenderWindowInteractor
from ccpi.viewer import viewer2D, viewer3D


class QCILViewer3DToolBar(QtWidgets.QToolBar):
    def __init__(self, parent=None, viewer=None, **kwargs):
        '''
        Parameters
        -----------
        viewer: an instance of viewer2D or viewer3D
            the viewer which the toolbar is for. The viewer instance
            is passed to allow interactions to be controlled using the
            toolbar.

        '''
        super(QCILViewer3DToolBar, self).__init__(parent=parent, **kwargs)
        button1 = QtWidgets.QToolButton()
        button1.setText("1")
        button2 = QtWidgets.QToolButton()
        button2.setText("2")
        self.addWidget(button1)
        self.addWidget(button2)
