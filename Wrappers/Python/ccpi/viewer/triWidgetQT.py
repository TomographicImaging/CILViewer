# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/vdn73631/Desktop/frametest.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

# from ccpi.viewer.QVTKCILViewer import QVTKCILViewer
# from ccpi.viewer.QVTKUndirectedGraph import QVTKUndirectedGraph
# from ccpi.viewer.QVTKCILViewer3D import QVTKCILViewer3D

from ccpi.viewer.CILViewer2D import CILViewer2D
from ccpi.viewer.CILViewer import CILViewer
from ccpi.viewer.undirected_graph import UndirectedGraph

from ccpi.viewer.QVTKWidget import QVTKWidget
from ccpi.viewer.undirected_graph import generate_data
import vtk

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # Central widget layout
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")

        # Add the 2D viewer widget
        self.viewerWidget = QVTKWidget(viewer=CILViewer2D)
        self.horizontalLayout.addWidget(self.viewerWidget, 66)

        # Add data to the viewer
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName("../../../../../data/head.mha")
        reader.Update()
        self.viewerWidget.viewer.setInput3DData(reader.GetOutput())

        # Create the vertical layout to handle the other displays
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")

        # Add the graph widget
        self.graphWidget = QVTKWidget(viewer=UndirectedGraph)
        self.verticalLayout.addWidget(self.graphWidget)
        self.graphWidget.viewer.update(generate_data())

        # Add the 3D viewer widget
        self.viewer3DWidget = QVTKWidget(viewer=CILViewer)
        self.verticalLayout.addWidget(self.viewer3DWidget)
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName("../../../../../data/head.mha")
        reader.Update()
        self.viewer3DWidget.viewer.setInput3DData(reader.GetOutput())

        # Add vertical layout to main layout
        self.horizontalLayout.addLayout(self.verticalLayout, 33)

        # Set central widget
        MainWindow.setCentralWidget(self.centralwidget)

        # Create menu bar
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 714, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)

        #Create status bar
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

