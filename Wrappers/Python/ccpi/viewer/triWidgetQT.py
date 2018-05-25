# -*- coding: utf-8 -*-



# Import viewer classes
from ccpi.viewer.CILViewer2D import CILViewer2D, Converter
from ccpi.viewer.CILViewer import CILViewer
from ccpi.viewer.undirected_graph import UndirectedGraph

# Import Class to convert vtk render window to QT widget
from ccpi.viewer.QVTKWidget import QVTKWidget

# Import temporary function to generate data for the graph view
# Will be replaced to read the data from the loaded image.
from ccpi.viewer.undirected_graph import generate_data

# Import modules requred to run the QT application
from PyQt5 import QtCore, QtGui, QtWidgets, Qt
import vtk
from natsort import natsorted
import imghdr

# Import linking class to join 2D and 3D viewers
import ccpi.viewer.viewerLinker as vlink

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

        # Set linked state
        self.linked = True

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # Central widget layout
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")

        # Add the 2D viewer widget
        self.viewerWidget = QVTKWidget(viewer=CILViewer2D, interactorStyle=vlink.Linked2DInteractorStyle)
        self.horizontalLayout.addWidget(self.viewerWidget, 66)

        # Create the vertical layout to handle the other displays
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")

        # Add the graph widget
        self.graphWidget = QVTKWidget(viewer=UndirectedGraph)
        self.verticalLayout.addWidget(self.graphWidget)
        self.graphWidget.viewer.update(generate_data())

        # Add the 3D viewer widget
        self.viewer3DWidget = QVTKWidget(viewer=CILViewer, interactorStyle=vlink.Linked3DInteractorStyle)
        self.verticalLayout.addWidget(self.viewer3DWidget)

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

        # Initially link viewers
        self.linkedViewersSetup()
        self.link2D3D.enable()

        self.toolbar()

        self.e = ErrorObserver()


    def toolbar(self):
        # Initialise the toolbar
        self.toolbar = self.mainwindow.addToolBar('Viewer tools')

        # define actions
        open_icon = QtGui.QIcon()
        openAction = QtWidgets.QAction(self.mainwindow.style().standardIcon(QtWidgets.QStyle.SP_DirOpenIcon), 'Open file', self.mainwindow)
        openAction.triggered.connect(self.openFile)

        save_icon = QtGui.QIcon()
        saveAction = QtWidgets.QAction(self.mainwindow.style().standardIcon(QtWidgets.QStyle.SP_DialogSaveButton), 'Save current render as PNG', self.mainwindow)
        # saveAction.setShortcut("Ctrl+S")
        saveAction.triggered.connect(self.saveFile)

        plus_icon = QtGui.QIcon()
        plus_icon.addPixmap(QtGui.QPixmap('icons/plus.png'),QtGui.QIcon.Normal, QtGui.
                            QIcon.Off)
        connectGraphAction = QtWidgets.QAction(plus_icon, 'Set Graph Widget parameters', self.mainwindow)
        connectGraphAction.triggered.connect(self.createDockableWindow)

        link_icon = QtGui.QIcon()
        link_icon.addPixmap(QtGui.QPixmap('icons/link.png'),QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.linkViewersAction = QtWidgets.QAction(link_icon,'Toggle link between 2D and 3D viewers', self.mainwindow)
        self.linkViewersAction.triggered.connect(self.toggleLink)

        # Add actions to toolbar
        self.toolbar.addAction(openAction)
        self.toolbar.addAction(saveAction)
        self.toolbar.addAction(connectGraphAction)
        self.toolbar.addAction(self.linkViewersAction)

    def linkedViewersSetup(self):
        self.link2D3D = vlink.ViewerLinker(self.viewerWidget.viewer, self.viewer3DWidget.viewer)
        self.link2D3D.setLinkPan(False)
        self.link2D3D.setLinkZoom(False)
        self.link2D3D.setLinkWindowLevel(True)
        self.link2D3D.setLinkSlice(True)

    def toggleLink(self):
        link_icon = QtGui.QIcon()
        link_icon.addPixmap(QtGui.QPixmap('icons/link.png'),QtGui.QIcon.Normal, QtGui.QIcon.Off)

        link_icon_broken = QtGui.QIcon()
        link_icon_broken.addPixmap(QtGui.QPixmap('icons/broken_link.png'),QtGui.QIcon.Normal, QtGui.QIcon.Off)

        if self.linked:
            self.link2D3D.disable()
            self.linkViewersAction.setIcon(link_icon_broken)
            self.linked = False

        else:
            self.link2D3D.enable()
            self.linkViewersAction.setIcon(link_icon)
            self.linked = True


    def createDockableWindow(self):
        self.graphDockWidget = QtWidgets.QDockWidget(self.mainwindow)
        self.graphDockWidget.setObjectName("dockWidget_3")
        self.graphDockWidgetContents = QtWidgets.QWidget()
        self.graphDockWidgetContents.setObjectName("dockWidgetContents_3")

        # Add vertical layout to dock contents
        self.graphDockVL = QtWidgets.QVBoxLayout(self.graphDockWidgetContents)
        self.graphDockVL.setContentsMargins(0, 0, 0, 0)
        self.graphDockVL.setObjectName("verticalLayout_3")

        # Create widget for dock contents
        self.dockWidget = QtWidgets.QWidget(self.graphDockWidgetContents)
        self.dockWidget.setObjectName("widget")

        # Add vertical layout to dock widget
        self.graphWidgetVL = QtWidgets.QVBoxLayout(self.dockWidget)
        self.graphWidgetVL.setContentsMargins(0, 0, 0, 0)
        self.graphWidgetVL.setObjectName("verticalLayout_3")

        # Add group box
        self.graphParamsGroupBox = QtWidgets.QGroupBox(self.dockWidget)
        self.graphParamsGroupBox.setObjectName("groupBox")
        self.graphParamsGroupBox.setTitle("Graph Parameters")

        # Add form layout to group box
        self.graphWidgetFL = QtWidgets.QFormLayout(self.graphParamsGroupBox)
        self.graphWidgetFL.setObjectName("formLayout_2")

        # Create validation rule for text entry
        validator = QtGui.QDoubleValidator()
        validator.setDecimals(3)

        # Add first field
        self.fieldLabel_1 = QtWidgets.QLabel(self.graphParamsGroupBox)
        self.fieldLabel_1.setObjectName("fieldLabel1")
        self.fieldLabel_1.setText("Value 1")
        self.graphWidgetFL.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.fieldLabel_1)
        self.lineEdit_1= QtWidgets.QLineEdit(self.graphParamsGroupBox)
        self.lineEdit_1.setObjectName("lineEdit_1")
        self.lineEdit_1.setValidator(validator)
        self.graphWidgetFL.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.lineEdit_1)

        # Add second field
        self.fieldLabel_2 = QtWidgets.QLabel(self.graphParamsGroupBox)
        self.fieldLabel_2.setObjectName("fieldLabel_2")
        self.fieldLabel_2.setText("Value 2")
        self.graphWidgetFL.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.fieldLabel_2)
        self.lineEdit_2 = QtWidgets.QLineEdit(self.graphParamsGroupBox)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.lineEdit_2.setValidator(validator)

        self.graphWidgetFL.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.lineEdit_2)

        # Add third field
        self.fieldLabel_3 = QtWidgets.QLabel(self.graphParamsGroupBox)
        self.fieldLabel_3.setObjectName("fieldLabel_3")
        self.fieldLabel_3.setText("Value 3")
        self.graphWidgetFL.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.fieldLabel_3)
        self.lineEdit_3 = QtWidgets.QLineEdit(self.graphParamsGroupBox)
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.lineEdit_3.setValidator(validator)

        self.graphWidgetFL.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.lineEdit_3)

        # Add submit button
        self.graphParamsSubmitButton = QtWidgets.QPushButton(self.graphParamsGroupBox)
        self.graphParamsSubmitButton.setObjectName("graphParamsSubmitButton")
        self.graphParamsSubmitButton.setText("Update")
        self.graphParamsSubmitButton.clicked.connect(self.updateGraph)
        self.graphWidgetFL.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.graphParamsSubmitButton)

        # Add elements to layout
        self.graphWidgetVL.addWidget(self.graphParamsGroupBox)
        self.graphDockVL.addWidget(self.dockWidget)
        self.graphDockWidget.setWidget(self.graphDockWidgetContents)
        self.mainwindow.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.graphDockWidget)

    def updateGraph(self):
        val1 = float(self.lineEdit_1.text())
        val2 = float(self.lineEdit_2.text())
        val3 = float(self.lineEdit_3.text())

        print (val1, val2, val3)

    def openFile(self):
        fn = QtWidgets.QFileDialog.getOpenFileNames(self.mainwindow, 'Open File','../../../../../data')

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
                    self.mainwindow.displayFileErrorDialog(file)
                    return

            # Have passed basic test, can attempt to load
            numpy_image = Converter.tiffStack2numpyEnforceBounds(filenames=filenames)
            reader = Converter.numpy2vtkImporter(numpy_image)
            reader.Update()

        if self.e.ErrorOccurred():
            self.mainwindow.displayFileErrorDialog(file)

        else:
            self.viewerWidget.viewer.setInput3DData(reader.GetOutput())
            self.viewer3DWidget.viewer.setInput3DData(reader.GetOutput())

            self.mainwindow.setStatusTip('Ready')

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


def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


