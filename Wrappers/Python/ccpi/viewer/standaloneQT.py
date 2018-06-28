import sys
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import *
import vtk
from ccpi.viewer.QVTKCILViewer import QVTKCILViewer
from ccpi.viewer.CILViewer2D import Converter
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
        self.iren = self.vtkWidget.getInteractor()
        self.vl.addWidget(self.vtkWidget)

        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)

        self.toolbar()

        self.statusBar()
        self.setStatusTip('Open file to begin visualisation...')

        self.show()

    def toolbar(self):
        # Initialise the toolbar
        self.toolbar = self.addToolBar('Viewer tools')

        # define actions
        openAction = QAction(self.style().standardIcon(QStyle.SP_DirOpenIcon), 'Open file', self)
        openAction.triggered.connect(self.openFile)

        saveAction = QAction(self.style().standardIcon(QStyle.SP_DialogSaveButton), 'Save current render as PNG', self)
        # saveAction.setShortcut("Ctrl+S")
        saveAction.triggered.connect(self.saveFile)

        # Add actions to toolbar
        self.toolbar.addAction(openAction)
        self.toolbar.addAction(saveAction)


    def openFile(self):
        fn = QFileDialog.getOpenFileNames(self, 'Open File')

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
                    self.displayFileErrorDialog(file)
                    return

            # Have passed basic test, can attempt to load
            numpy_image = Converter.tiffStack2numpyEnforceBounds(filenames=filenames)
            reader = Converter.numpy2vtkImporter(numpy_image)
            reader.Update()

        if self.e.ErrorOccurred():
            self.displayFileErrorDialog(file)

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

    def displayFileErrorDialog(self, file):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("READ ERROR")
        msg.setText("Error reading file: ({filename})".format(filename=file))
        msg.setDetailedText(self.e.ErrorMessage())
        msg.exec_()


    def close(self):
        qApp.quit()


def main():

    App = QApplication(sys.argv)
    gui = Window()
    sys.exit(App.exec())

if __name__=="__main__":
    main()