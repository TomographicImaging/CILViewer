import sys
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import *
import vtk
from ccpi.viewer.QVTKCILViewer import QVTKCILViewer

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

class Window(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('CIL Viewer')
        self.setGeometry(50, 50, 600, 600)

        self.e = ErrorObserver()

        openAction = QAction("Open", self)
        openAction.setShortcut("Ctrl+O")
        openAction.triggered.connect(self.openFile)

        closeAction = QAction("Close", self)
        closeAction.setShortcut("Ctrl+Q")
        closeAction.triggered.connect(self.close)

        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(closeAction)

        self.frame = QFrame()
        self.vl = QVBoxLayout()
        self.vtkWidget = QVTKCILViewer(self.frame)
        self.iren = self.vtkWidget.GetInteractor()
        self.vl.addWidget(self.vtkWidget)

        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)

        self.toolbar()

        self.statusBar()
        self.setStatusTip('Open file to begin visualiser...')

        self.show()

    def toolbar(self):
        # Initialise the toolbar
        self.toolbar = self.addToolBar('Viewer tools')

        # define actions
        openAction = QAction(self.style().standardIcon(QStyle.SP_DirOpenIcon), 'Open file', self)
        openAction.triggered.connect(self.openFile)

        saveAction = QAction(self.style().standardIcon(QStyle.SP_DialogSaveButton), 'Save current render as PNG', self)
        saveAction.setShortcut("Ctrl+S")
        saveAction.triggered.connect(self.saveFile)

        # Add actions to toolbar
        self.toolbar.addAction(openAction)
        self.toolbar.addAction(saveAction)


    def openFile(self):
        fn = QFileDialog.getOpenFileName(self, 'Open File')

        reader = vtk.vtkMetaImageReader()
        reader.AddObserver("ErrorEvent", self.e)
        reader.SetFileName(fn[0])
        reader.Update()

        if self.e.ErrorOccurred():
            if fn[0]:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("READ ERROR")
                msg.setText("Error reading file: ({})".format(fn[0]))
                msg.setDetailedText(self.e.ErrorMessage())
                msg.exec_()

        else:
            self.vtkWidget.viewer.setInput3DData(reader.GetOutput())

        self.setStatusTip('Ready')


    def saveFile(self):
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptSave)

        fn = dialog.getSaveFileName(self,'Save As','.',"Images (*.png)")

        # Only save if the user has selected a name
        if fn[0]:
            self.vtkWidget.viewer.saveRender(fn[0])

    def close(self):
        qApp.quit()

App = QApplication(sys.argv)
gui = Window()
sys.exit(App.exec())