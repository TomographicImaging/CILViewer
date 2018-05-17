# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/vdn73631/Desktop/frametest.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

from ccpi.viewer.CILViewer2D import CILViewer2D, Converter
from ccpi.viewer.CILViewer import CILViewer
from ccpi.viewer.undirected_graph import UndirectedGraph

from ccpi.viewer.QVTKWidget import QVTKWidget
from ccpi.viewer.undirected_graph import generate_data
import vtk

from natsort import natsorted
import imghdr

class ErrorObserver:

   def __init__(self):
       self.__ErrorOccurred = False
       self.__ErrorMessage = None
       self.CallDataType = 'string0'

   def __call__(self, obj, event, message):
       self.__ErrorOccurred = True
       self.__ErrorMessage = message

   def ErrorOccurred(self):
       occ = self.__ErrorOccurred
       self.__ErrorOccurred = False
       return occ

   def ErrorMessage(self):
       return self.__ErrorMessage


def sentenceCase(string):
    if string:
        first_word = string.split()[0]
        world_len = len(first_word)

        return first_word.capitalize() + string[world_len:]

    else:
        return ''

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        self.mainwindow = MainWindow
        MainWindow.setObjectName("CIL Viewer")
        MainWindow.setWindowTitle("CIL Viewer")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # Central widget layout
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")

        # Add the 2D viewer widget
        self.viewerWidget = QVTKWidget(viewer=CILViewer2D)
        self.horizontalLayout.addWidget(self.viewerWidget, 66)

        # # Add data to the viewer
        # reader = vtk.vtkMetaImageReader()
        # reader.SetFileName("../../../../../data/head.mha")
        # reader.Update()
        # self.viewerWidget.viewer.setInput3DData(reader.GetOutput())

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
        # reader = vtk.vtkMetaImageReader()
        # reader.SetFileName("../../../../../../data/head.mha")
        # reader.Update()
        # self.viewer3DWidget.viewer.setInput3DData(reader.GetOutput())

        # Add vertical layout to main layout
        self.horizontalLayout.addLayout(self.verticalLayout, 33)

        # Set central widget
        MainWindow.setCentralWidget(self.centralwidget)

        # Create menu actions
        openAction = QtWidgets.QAction("Open", MainWindow)
        openAction.setShortcut("Ctrl+O")
        openAction.triggered.connect(self.openFile)

        closeAction = QtWidgets.QAction("Close", MainWindow)
        closeAction.setShortcut("Ctrl+Q")
        closeAction.triggered.connect(self.close)

        #Create status bar
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusTip('Open file to begin visualisation...')
        MainWindow.setStatusBar(self.statusbar)

        self.toolbar()

        self.e = ErrorObserver()

    def toolbar(self):
        # Initialise the toolbar
        self.toolbar = self.mainwindow.addToolBar('Viewer tools')

        # define actions
        openAction = QtWidgets.QAction(self.mainwindow.style().standardIcon(QtWidgets.QStyle.SP_DirOpenIcon), 'Open file', self.mainwindow)
        openAction.triggered.connect(self.openFile)

        saveAction = QtWidgets.QAction(self.mainwindow.style().standardIcon(QtWidgets.QStyle.SP_DialogSaveButton), 'Save current render as PNG', self.mainwindow)
        # saveAction.setShortcut("Ctrl+S")
        saveAction.triggered.connect(self.saveFile)

        # Add actions to toolbar
        self.toolbar.addAction(openAction)
        self.toolbar.addAction(saveAction)

    def openFile(self):
        fn = QtWidgets.QFileDialog.getOpenFileNames(MainWindow, 'Open File','../../../../../data')

        # If the user has pressed cancel, the first element of the tuple will be empty.
        # Quit the method cleanly
        if not fn[0]:
            return

        # Single file selection
        if len(fn[0]) == 1:
            file = fn[0][0]

            reader = vtk.vtkMetaImageReader()
            reader.AddObserver("ErrorEvent", self.e)
            reader.SetFileName(file)
            reader.Update()

        # Multiple TIFF files selected
        else:
            # Make sure that the files are sorted 0 - end
            filenames = natsorted(fn[0])

            # Basic test for tiff images
            for file in filenames:
                ftype = imghdr.what(file)
                if ftype != 'tiff':
                    # A non-TIFF file has been loaded, present error message and exit method
                    self.e('','','When reading multiple files, all files must TIFF formatted.')
                    file = file
                    MainWindow.displayFileErrorDialog(file)
                    return

            # Have passed basic test, can attempt to load
            numpy_image = Converter.tiffStack2numpyEnforceBounds(filenames=filenames)
            reader = Converter.numpy2vtkImporter(numpy_image)
            reader.Update()

        if self.e.ErrorOccurred():
            MainWindow.displayFileErrorDialog(file)

        else:
            self.viewerWidget.viewer.setInput3DData(reader.GetOutput())
            self.viewer3DWidget.viewer.setInput3DData(reader.GetOutput())

            MainWindow.setStatusTip('Ready')

    def saveFile(self):
        dialog = QtWidgets.QFileDialog(self.mainwindow)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)

        fn = dialog.getSaveFileName(self.mainwindow,'Save As','.',"Images (*.png)")

        # Only save if the user has selected a name
        if fn[0]:
            self.viewerWidget.viewer.saveRender(fn[0])

    def close(self):
        QtWidgets.qApp.quit()

    def displayFileErrorDialog(self, file):
        msg = QtWidgets.QMessageBox(self.mainwindow)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle("READ ERROR")
        msg.setText("Error reading file: ({filename})".format(filename=file))
        msg.setDetailedText(self.e.ErrorMessage())
        msg.exec_()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

