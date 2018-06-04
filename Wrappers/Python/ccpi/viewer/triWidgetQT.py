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

# Import segmenation algorithm and tools
from ccpi.segmentation.SimpleflexSegmentor import SimpleflexSegmentor
import numpy

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

        # Set numpy data array for graph
        self.graph_numpy_input_data = None

        # Dockable window flag
        self.hasDockableWindow = False

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
        # self.graphWidget.viewer.update(generate_data())

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
        openAction = QtWidgets.QAction(self.mainwindow.style().standardIcon(QtWidgets.QStyle.SP_DirOpenIcon), 'Open file', self.mainwindow)
        openAction.triggered.connect(self.openFile)

        saveAction = QtWidgets.QAction(self.mainwindow.style().standardIcon(QtWidgets.QStyle.SP_DialogSaveButton), 'Save current render as PNG', self.mainwindow)
        saveAction.triggered.connect(self.saveFile)

        tree_icon = QtGui.QIcon()
        tree_icon.addPixmap(QtGui.QPixmap('icons/tree_icon.png'),QtGui.QIcon.Normal, QtGui.
                            QIcon.Off)
        connectGraphAction = QtWidgets.QAction(tree_icon, 'Set Graph Widget parameters', self.mainwindow)
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

    # def closeEvent(self):
    #     print ("Closing")

    def createDockableWindow(self):

        # Check if the dockable window has already been created
        if self.hasDockableWindow:

            # If the dockable window has already been created and is visible then don't add another one
            if self.graphDockWidget.isVisible():
                return
            else:
                # If the dockable window has already been created and is not visible. Set it to visible and return
                self.graphDockWidget.setVisible(True)
                return

        # The dockable window has been activated for the first time.
        # Set the hasDockableWindow flag
        self.hasDockableWindow = True

        # Keep a collection of related elements to set enabled/disabled state
        self.treeWidgetInitialElements = []
        self.treeWidgetUpdateElements = []

        # Setup segmentation
        self.segmentor = SimpleflexSegmentor()

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
        validator.setDecimals(2)

        # Add button to run graphing function
        self.graphStart = QtWidgets.QPushButton(self.graphParamsGroupBox)
        self.graphStart.setObjectName("graphStart")
        self.graphStart.setText("Generate Graph")
        self.graphStart.clicked.connect(self.generateGraph)
        self.graphWidgetFL.setWidget(0, QtWidgets.QFormLayout.SpanningRole, self.graphStart)
        self.treeWidgetInitialElements.append(self.graphStart)

        # Add horizonal seperator
        self.seperator = QtWidgets.QFrame(self.graphParamsGroupBox)
        self.seperator.setFrameShape(QtWidgets.QFrame.HLine)
        self.seperator.setFrameShadow(QtWidgets.QFrame.Raised)
        self.graphWidgetFL.setWidget(1, QtWidgets.QFormLayout.SpanningRole, self.seperator)


        # Add ISO Value field
        self.isoValueLabel = QtWidgets.QLabel(self.graphParamsGroupBox)
        self.isoValueLabel.setObjectName("fieldLabel1")
        self.isoValueLabel.setText("Iso Value (%)")
        self.graphWidgetFL.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.isoValueLabel)
        self.isoValueEntry= QtWidgets.QLineEdit(self.graphParamsGroupBox)
        self.isoValueEntry.setObjectName("lineEdit_1")
        self.isoValueEntry.setValidator(validator)
        self.isoValueEntry.setText("35")
        self.graphWidgetFL.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.isoValueEntry)
        self.treeWidgetUpdateElements.append(self.isoValueEntry)
        self.treeWidgetUpdateElements.append(self.isoValueLabel)

        # Add local/global checkbox
        self.isGlobalCheck = QtWidgets.QCheckBox(self.graphParamsGroupBox)
        self.isGlobalCheck.setText("Global Iso")
        self.isGlobalCheck.setChecked(True)
        self.graphWidgetFL.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.isGlobalCheck)
        self.treeWidgetUpdateElements.append(self.isGlobalCheck)

        # Add Log Tree field
        self.logTreeValueLabel = QtWidgets.QLabel(self.graphParamsGroupBox)
        self.logTreeValueLabel.setObjectName("fieldLabel_2")
        self.logTreeValueLabel.setText("Log Tree Size")
        self.graphWidgetFL.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.logTreeValueLabel)
        self.logTreeValueEntry = QtWidgets.QLineEdit(self.graphParamsGroupBox)
        self.logTreeValueEntry.setObjectName("lineEdit_2")
        self.logTreeValueEntry.setValidator(validator)
        self.logTreeValueEntry.setText("0.34")
        self.treeWidgetUpdateElements.append(self.logTreeValueEntry)
        self.treeWidgetUpdateElements.append(self.logTreeValueLabel)


        self.graphWidgetFL.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.logTreeValueEntry)

        # Add third field
        self.collapsePriorityLabel = QtWidgets.QLabel(self.graphParamsGroupBox)
        self.collapsePriorityLabel.setObjectName("fieldLabel_3")
        self.collapsePriorityLabel.setText("Collapse Priority")
        self.graphWidgetFL.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.collapsePriorityLabel)
        self.collapsePriorityValue = QtWidgets.QComboBox(self.graphParamsGroupBox)
        self.collapsePriorityValue.setObjectName("comboBox")
        self.collapsePriorityValue.addItem("Height")
        self.collapsePriorityValue.addItem("Volume")
        self.collapsePriorityValue.addItem("Hypervolume")
        self.collapsePriorityValue.addItem("Approx Hypervolume")
        self.collapsePriorityValue.setCurrentIndex(1)
        self.treeWidgetUpdateElements.append(self.collapsePriorityValue)
        self.treeWidgetUpdateElements.append(self.collapsePriorityLabel)


        self.graphWidgetFL.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.collapsePriorityValue)

        # Add submit button
        self.graphParamsSubmitButton = QtWidgets.QPushButton(self.graphParamsGroupBox)
        self.graphParamsSubmitButton.setObjectName("graphParamsSubmitButton")
        self.graphParamsSubmitButton.setText("Update")
        self.graphParamsSubmitButton.clicked.connect(self.updateGraph)
        self.graphWidgetFL.setWidget(6, QtWidgets.QFormLayout.FieldRole, self.graphParamsSubmitButton)
        self.treeWidgetUpdateElements.append(self.graphParamsSubmitButton)


        # Add elements to layout
        self.graphWidgetVL.addWidget(self.graphParamsGroupBox)
        self.graphDockVL.addWidget(self.dockWidget)
        self.graphDockWidget.setWidget(self.graphDockWidgetContents)
        self.mainwindow.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.graphDockWidget)

        # Set update elements to disabled when first opening the window
        if self.graph_numpy_input_data is None:
            for element in self.treeWidgetUpdateElements:
                element.setEnabled(False)


    def updateGraph(self):
        # Set parameter values
        isoVal = float(self.isoValueEntry.text())
        logTreeVal = float(self.logTreeValueEntry.text())
        self.segmentor.collapsePriority = self.collapsePriorityValue.currentIndex()

        # Make sure to set the LocalIsoValue when isGlobal is false (ie. Local)
        if self.isGlobalCheck.isChecked():
            self.segmentor.setIsoValuePercent(isoVal)
        else:
            self.segmentor.setLocalIsoValuePercent(isoVal)

        # Update tree
        self.segmentor.updateTreeFromLogTreeSize(logTreeVal, self.isGlobalCheck.isChecked())

        # Display results
        self.displaySurfaces()
        self.displayTree()

    def generateGraph(self):

        if self.graph_numpy_input_data is not None:

            self.segmentor.setInputData(self.graph_numpy_input_data)
            self.segmentor.calculateContourTree()

            self.segmentor.setIsoValuePercent(float(self.isoValueEntry.text()))
            self.segmentor.collapsePriority = self.collapsePriorityValue.currentIndex()
            self.segmentor.updateTreeFromLogTreeSize(float(self.logTreeValueEntry.text()), self.isGlobalCheck.isChecked())

            # Display results
            self.displaySurfaces()
            self.displayTree()

            # Once the graph has generated allow editing of the values and disable the generate button
            for element in self.treeWidgetUpdateElements:
                element.setEnabled(True)

            for element in self.treeWidgetInitialElements:
                element.setEnabled(False)
        else:
            msg = QtWidgets.QMessageBox(self.mainwindow)
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setWindowTitle("NO DATA")
            msg.setText("No data has been loaded into the reader. Please load a file to run the graph.")
            msg.exec_()



    def displayTree(self):
        tree = self.segmentor.getContourTree()

        self.graphWidget.viewer.updateCornerAnnotation("featureAnnotation", "Features: {}".format(len(tree)/2))

        graph = vtk.vtkMutableDirectedGraph()
        X = vtk.vtkDoubleArray()
        X.SetNumberOfComponents(1)
        X.SetName("X")

        Y = vtk.vtkDoubleArray()
        Y.SetNumberOfComponents(1)
        Y.SetName("Y")

        weights = vtk.vtkDoubleArray()
        weights.SetNumberOfComponents(1)
        weights.SetName("Weights")

        print("creating graph")
        # Adding to graph now
        N = int(len(tree) / 2)

        # normalise the values in Y
        # transpose tree
        treeT = list(zip(*tree))
        maxY = max(treeT[1])
        minY = min(treeT[1])
        deltaY = maxY - minY
        print(minY, maxY, deltaY)
        maxX = max(treeT[0])
        minX = min(treeT[0])
        deltaX = maxX - minX
        print(minX, maxX, deltaX)

        for i in range(N):
            even = 2 * i
            odd = even + 1
            if odd >= len(tree):
                raise ValueError('out of bounds')
            v = [tree[2 * i], tree[2 * i + 1]]

            # print(i, even, odd, "Adding",v[0],v[1])
            v1 = graph.AddVertex()
            v2 = graph.AddVertex()
            graph.AddEdge(v1, v2)

            # Insert XY as a % of max range
            X.InsertNextValue((v[0][0] - minX)/deltaX )
            X.InsertNextValue((v[1][0] - minX) / deltaX )

            Y.InsertNextValue((v[0][1] - minY)/ deltaY)
            Y.InsertNextValue((v[1][1] - minY)/ deltaY )

            weights.InsertNextValue(1.)
        print("Finished")  # Execution reaches here, error seems to be in cleanup upon closing

        graph.GetVertexData().AddArray(X)
        graph.GetVertexData().AddArray(Y)
        graph.GetEdgeData().AddArray(weights)

        print("Added Data")
        layoutStrategy = vtk.vtkAssignCoordinatesLayoutStrategy()
        layoutStrategy.SetYCoordArrayName('Y')
        layoutStrategy.SetXCoordArrayName('X')

        self.graphWidget.viewer.update(graph)

    def displaySurfaces(self):
        #Display isosurfaces in 3D
        # Create the VTK output
        # Points coordinates structure
        triangle_vertices = vtk.vtkPoints()

        # associate the points to triangles
        triangle = vtk.vtkTriangle()

        # put all triangles in an array
        triangles = vtk.vtkCellArray()
        isTriangle = 0
        nTriangle = 0

        surface = 0
        # associate each coordinate with a point: 3 coordinates are needed for a point
        # in 3D. Additionally we perform a shift from image coordinates (pixel) which
        # is the default of the Contour Tree Algorithm to the World Coordinates.

        origin = self.origin
        spacing = self.spacing

        # augmented matrix for affine transformations
        mScaling = numpy.asarray([spacing[0], 0, 0, 0,
                                  0, spacing[1], 0, 0,
                                  0, 0, spacing[2], 0,
                                  0, 0, 0, 1]).reshape((4, 4))
        mShift = numpy.asarray([1, 0, 0, origin[0],
                                0, 1, 0, origin[1],
                                0, 0, 1, origin[2],
                                0, 0, 0, 1]).reshape((4, 4))

        mTransform = numpy.dot(mScaling, mShift)
        point_count = 0

        surf_list = self.segmentor.getSurfaces()

        for surf in surf_list:
            print("Image-to-world coordinate trasformation ... %d" % surface)
            for point in surf:
                world_coord = numpy.dot(mTransform, point)
                xCoord = world_coord[0]
                yCoord = world_coord[1]
                zCoord = world_coord[2]
                triangle_vertices.InsertNextPoint(xCoord, yCoord, zCoord);

                # The id of the vertex of the triangle (0,1,2) is linked to
                # the id of the points in the list, so in facts we just link id-to-id
                triangle.GetPointIds().SetId(isTriangle, point_count)
                isTriangle += 1
                point_count += 1

                if (isTriangle == 3):
                    isTriangle = 0;
                    # insert the current triangle in the triangles array
                    triangles.InsertNextCell(triangle);

        surface += 1

        # polydata object
        trianglePolyData = vtk.vtkPolyData()
        trianglePolyData.SetPoints(triangle_vertices)
        trianglePolyData.SetPolys(triangles)

        self.viewer3DWidget.viewer.hideActor(1, delete = True)
        self.viewer3DWidget.viewer.displayPolyData(trianglePolyData)

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
            # numpy_image = Converter.tiffStack2numpyEnforceBounds(filenames=filenames, bounds=(256,256,256))
            numpy_image = Converter.pureTiff2Numpy(filenames=filenames, bounds=(256,246,256))
            reader = Converter.numpy2vtkImporter(numpy_image)
            reader.Update()

        if self.e.ErrorOccurred():
            self.mainwindow.displayFileErrorDialog(file)

        else:
            self.viewerWidget.viewer.setInput3DData(reader.GetOutput())
            self.viewer3DWidget.viewer.setInput3DData(reader.GetOutput())
            self.graph_numpy_input_data = Converter.vtk2numpy(reader.GetOutput(), transpose=[2,1,0])
            self.mainwindow.setStatusTip('Ready')
            self.spacing = reader.GetOutput().GetSpacing()
            self.origin = reader.GetOutput().GetOrigin()

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


