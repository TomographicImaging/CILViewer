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

import sys, traceback


class ReadError(Exception):
    """Raised when there is a problem reading the file into vtk"""


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

class Worker(QtCore.QRunnable):
    """
    Worker thread

    Inherits from QRunnable to handle worker thread setup, signals and wrapup.

    :param (function) callback:
        The function callback to run on this worker thread. Supplied
        args/kwargs will be pass to the runner.

    :param args:
        Arguments to pass to the callback function

    :param kwargs:
        Keyword arguments to pass to the callback function

    """
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add progress callback to kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @QtCore.pyqtSlot()
    def run(self):
        """
        Run the worker. Emits signals based on run state.
        Signals:
            - Error: Emitted when an exception is thrown in the workers function.
            - Result: Emitted if function completes successfully. Contains the return value of the function.
            - Finished: Emitted on completion of the worker thread.

        """
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

class WorkerSignals(QtCore.QObject):
    """
    Defines signals available when running a worker thread
    Supported Signals:
    finished
        No Data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress
    """

    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(tuple)
    result = QtCore.pyqtSignal(object)
    progress = QtCore.pyqtSignal(int)

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
        MainWindow.setWindowTitle("CIL Viewer")
        MainWindow.resize(800, 600)

        # Contains response from open file dialog
        self.fn = None

        # Set linked state
        self.linked = True

        # Create link icon for inital load state.
        link_icon = QtGui.QIcon()
        link_icon.addPixmap(QtGui.QPixmap('icons/link.png'), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        # Set numpy data array for graph
        self.graph_numpy_input_data = None

        # Dockable window flag
        self.hasDockableWindow = False

        self.centralwidget = QtWidgets.QWidget(MainWindow)

        # Central widget layout
        self.main_widget_form_layout = QtWidgets.QGridLayout(self.centralwidget)

        # Add the 2D viewer widget
        self.viewerWidget = QVTKWidget(viewer=CILViewer2D, interactorStyle=vlink.Linked2DInteractorStyle)
        self.centralwidget.setStyleSheet("background-color: rgb(25,51,101)")

        self.linkButton2D = QtWidgets.QPushButton(self.viewerWidget)
        self.linkButton2D.setIcon(link_icon)
        self.linkButton2D.setGeometry(0, 0, 30, 30)
        self.linkButton2D.setStyleSheet("background-color: whitesmoke")
        self.linkButton2D.setToolTip("State: Linked. Toggle status of link between 2D and 3D viewers")

        self.linkButton2D.clicked.connect(self.linkViewers)

        self.main_widget_form_layout.addWidget(self.linkButton2D, 0,0,1,1)
        self.main_widget_form_layout.addItem(QtWidgets.QSpacerItem(1,1,QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum),0,1,1,1)
        self.main_widget_form_layout.addWidget(self.viewerWidget,1,0,1,2)

        # Add the graph widget
        self.graphWidget = QVTKWidget(viewer=UndirectedGraph)

        self.graphDock = QtWidgets.QDockWidget(MainWindow)
        self.graphDock.setMinimumWidth(300)
        self.graphDock.setWidget(self.graphWidget)
        self.graphDock.setWindowTitle("Graph View")

        MainWindow.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.graphDock)

        # Add the 3D viewer widget
        self.viewer3DWidget = QVTKWidget(viewer=CILViewer, interactorStyle=vlink.Linked3DInteractorStyle)

        self.Dock3DContents = QtWidgets.QWidget()
        self.Dock3DContents.setStyleSheet("background-color: rgb(25,51,101)")
        f_layout3D = Qt.QFormLayout(self.Dock3DContents)

        self.Dock3D = QtWidgets.QDockWidget(MainWindow)
        self.Dock3D.setMinimumWidth(300)
        self.Dock3D.setWindowTitle("3D View")

        self.linkButton3D = QtWidgets.QPushButton(self.viewer3DWidget)
        self.linkButton3D.setIcon(link_icon)
        self.linkButton3D.setGeometry(0,0,30,30)
        self.linkButton3D.setStyleSheet("background-color: whitesmoke")
        self.linkButton3D.setToolTip("State: Linked. Toggle status of link between 2D and 3D viewers")

        self.linkButton3D.clicked.connect(self.linkViewers)

        f_layout3D.addWidget(self.linkButton3D)
        f_layout3D.addWidget(self.viewer3DWidget)
        self.Dock3D.setWidget(self.Dock3DContents)
        MainWindow.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.Dock3D)

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
        MainWindow.setStatusTip('Open file to begin visualisation...')
        MainWindow.setStatusBar(self.statusbar)

        # Initially link viewers
        self.linkedViewersSetup()
        self.link2D3D.enable()

        # Create the toolbar
        self.toolbar()

        # Add threading
        self.threadpool = QtCore.QThreadPool()
        self.e = ErrorObserver()

        # Add progress bar
        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setMaximumWidth(250)
        self.progressBar.hide()
        self.statusbar.addPermanentWidget(self.progressBar)

    def linkViewers(self, force_linked=False):

        link_icon = QtGui.QIcon()
        link_icon.addPixmap(QtGui.QPixmap('icons/link.png'), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        link_icon_broken = QtGui.QIcon()
        link_icon_broken.addPixmap(QtGui.QPixmap('icons/broken_link.png'), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        if self.linked and not force_linked:
            self.link2D3D.disable()
            self.linkButton3D.setIcon(link_icon_broken)
            self.linkButton2D.setIcon(link_icon_broken)
            self.linkButton3D.setToolTip("State: Un-linked. Toggle status of link between 2D and 3D viewers")
            self.linkButton2D.setToolTip("State: Un-linked. Toggle status of link between 2D and 3D viewers")
            self.linked = False

        else:
            self.link2D3D.enable()
            self.linkButton3D.setIcon(link_icon)
            self.linkButton2D.setIcon(link_icon)
            self.linkButton3D.setToolTip("State: Linked. Toggle status of link between 2D and 3D viewers")
            self.linkButton2D.setToolTip("State: Linked. Toggle status of link between 2D and 3D viewers")
            self.linked = True

    def toolbar(self):
        # Initialise the toolbar
        self.toolbar = self.mainwindow.addToolBar('Viewer tools')

        # define actions
        openAction = QtWidgets.QAction(self.mainwindow.style().standardIcon(QtWidgets.QStyle.SP_DirOpenIcon), 'Open file', self.mainwindow)
        openAction.triggered.connect(self.openFileTrigger)

        saveAction = QtWidgets.QAction(self.mainwindow.style().standardIcon(QtWidgets.QStyle.SP_DialogSaveButton), 'Save current render as PNG', self.mainwindow)
        saveAction.triggered.connect(self.saveFile)

        tree_icon = QtGui.QIcon()
        tree_icon.addPixmap(QtGui.QPixmap('icons/tree_icon.png'),QtGui.QIcon.Normal, QtGui.
                            QIcon.Off)
        connectGraphAction = QtWidgets.QAction(tree_icon, 'Set Graph Widget parameters', self.mainwindow)
        connectGraphAction.triggered.connect(self.createDockableWindow)



        show_icon = QtGui.QIcon()
        show_icon.addPixmap(QtGui.QPixmap('icons/show.png'),QtGui.QIcon.Normal, QtGui.
                            QIcon.Off)
        showWidgetsAction = QtWidgets.QAction(show_icon, 'Display tree and 3D viewer', self.mainwindow)
        showWidgetsAction.triggered.connect(self.dockWidgets)

        # Add actions to toolbar
        self.toolbar.addAction(openAction)
        self.toolbar.addAction(saveAction)
        self.toolbar.addAction(connectGraphAction)
        self.toolbar.addAction(showWidgetsAction)

    def linkedViewersSetup(self):
        self.link2D3D = vlink.ViewerLinker(self.viewerWidget.viewer, self.viewer3DWidget.viewer)
        self.link2D3D.setLinkPan(False)
        self.link2D3D.setLinkZoom(False)
        self.link2D3D.setLinkWindowLevel(True)
        self.link2D3D.setLinkSlice(True)

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
        self.graphDockWidgetContents = QtWidgets.QWidget()


        # Add vertical layout to dock contents
        self.graphDockVL = QtWidgets.QVBoxLayout(self.graphDockWidgetContents)
        self.graphDockVL.setContentsMargins(0, 0, 0, 0)

        # Create widget for dock contents
        self.dockWidget = QtWidgets.QWidget(self.graphDockWidgetContents)

        # Add vertical layout to dock widget
        self.graphWidgetVL = QtWidgets.QVBoxLayout(self.dockWidget)
        self.graphWidgetVL.setContentsMargins(0, 0, 0, 0)

        # Add group box
        self.graphParamsGroupBox = QtWidgets.QGroupBox(self.dockWidget)
        self.graphParamsGroupBox.setTitle("Graph Parameters")

        # Add form layout to group box
        self.graphWidgetFL = QtWidgets.QFormLayout(self.graphParamsGroupBox)

        # Create validation rule for text entry
        validator = QtGui.QDoubleValidator()
        validator.setDecimals(2)

        # Add button to run graphing function
        self.graphStart = QtWidgets.QPushButton(self.graphParamsGroupBox)
        self.graphStart.setText("Generate Graph")
        self.graphStart.clicked.connect(self.generateGraphTrigger)
        self.graphWidgetFL.setWidget(0, QtWidgets.QFormLayout.SpanningRole, self.graphStart)
        self.treeWidgetInitialElements.append(self.graphStart)

        # Add horizonal seperator
        self.seperator = QtWidgets.QFrame(self.graphParamsGroupBox)
        self.seperator.setFrameShape(QtWidgets.QFrame.HLine)
        self.seperator.setFrameShadow(QtWidgets.QFrame.Raised)
        self.graphWidgetFL.setWidget(1, QtWidgets.QFormLayout.SpanningRole, self.seperator)


        # Add ISO Value field
        self.isoValueLabel = QtWidgets.QLabel(self.graphParamsGroupBox)
        self.isoValueLabel.setText("Iso Value (%)")
        self.graphWidgetFL.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.isoValueLabel)
        self.isoValueEntry= QtWidgets.QLineEdit(self.graphParamsGroupBox)
        self.isoValueEntry.setValidator(validator)
        self.isoValueEntry.setText("35")
        self.graphWidgetFL.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.isoValueEntry)
        self.treeWidgetUpdateElements.append(self.isoValueEntry)
        self.treeWidgetUpdateElements.append(self.isoValueLabel)

        # Add local/global checkbox
        self.isGlobalCheck = QtWidgets.QCheckBox(self.graphParamsGroupBox)
        self.isGlobalCheck.setText("Global Iso")
        self.isGlobalCheck.setChecked(True)
        self.graphWidgetFL.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.isGlobalCheck)
        self.treeWidgetUpdateElements.append(self.isGlobalCheck)

        # Add colour surfaces checkbox
        self.surfaceColourCheck = QtWidgets.QCheckBox(self.graphParamsGroupBox)
        self.surfaceColourCheck.setText("Colour Surfaces")
        self.graphWidgetFL.setWidget(3,QtWidgets.QFormLayout.FieldRole, self.surfaceColourCheck)
        self.treeWidgetUpdateElements.append(self.surfaceColourCheck)

        # Add Log Tree field
        self.logTreeValueLabel = QtWidgets.QLabel(self.graphParamsGroupBox)
        self.logTreeValueLabel.setText("Log Tree Size")
        self.graphWidgetFL.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.logTreeValueLabel)
        self.logTreeValueEntry = QtWidgets.QLineEdit(self.graphParamsGroupBox)
        self.logTreeValueEntry.setValidator(validator)
        self.logTreeValueEntry.setText("0.34")
        self.treeWidgetUpdateElements.append(self.logTreeValueEntry)
        self.treeWidgetUpdateElements.append(self.logTreeValueLabel)

        self.graphWidgetFL.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.logTreeValueEntry)

        # Add collapse priority field
        self.collapsePriorityLabel = QtWidgets.QLabel(self.graphParamsGroupBox)
        self.collapsePriorityLabel.setText("Collapse Priority")
        self.graphWidgetFL.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.collapsePriorityLabel)
        self.collapsePriorityValue = QtWidgets.QComboBox(self.graphParamsGroupBox)
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
        self.graphParamsSubmitButton.setText("Update")
        self.graphParamsSubmitButton.clicked.connect(self.updateGraphTrigger)
        self.graphWidgetFL.setWidget(6, QtWidgets.QFormLayout.FieldRole, self.graphParamsSubmitButton)
        self.treeWidgetUpdateElements.append(self.graphParamsSubmitButton)

        # Add elements to layout
        self.graphWidgetVL.addWidget(self.graphParamsGroupBox)
        self.graphDockVL.addWidget(self.dockWidget)
        self.graphDockWidget.setWidget(self.graphDockWidgetContents)
        self.mainwindow.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.graphDockWidget)

        # Set update elements to disabled when first opening the window
        if self.segmentor.dimensions is None:
            for element in self.treeWidgetUpdateElements:
                element.setEnabled(False)

    def dockWidgets(self):
        """
        The 3D viewer widget and graph widget are Dockable windows. Once closed, they are hidden.
        This method makes them visible again.
        """

        self.Dock3D.show()
        self.graphDock.show()

    def updateGraph(self, progress_callback):
        """
        Make updates to the graph based on user input.

        :param (function) progress_callback:
            Function to perform to emit progress signal.

        """

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
        progress_callback.emit(30)

        # Display results
        self.displaySurfaces(progress_callback)
        self.displayTree()


    def generateGraph(self, progress_callback):
        """
        Generates the initial graph and 3D surface render

        :param (function) progress_callback:
            Function to perform to emit progress signal.

        """

        self.segmentor.setInputData(self.graph_numpy_input_data)
        progress_callback.emit(5)

        self.segmentor.calculateContourTree()
        progress_callback.emit(25)

        self.segmentor.setIsoValuePercent(float(self.isoValueEntry.text()))
        self.segmentor.collapsePriority = self.collapsePriorityValue.currentIndex()
        self.segmentor.updateTreeFromLogTreeSize(float(self.logTreeValueEntry.text()), self.isGlobalCheck.isChecked())
        progress_callback.emit(30)

        # Display results
        self.displaySurfaces(progress_callback)
        self.displayTree()

        # Once the graph has generated allow editing of the values and disable the generate button
        for element in self.treeWidgetUpdateElements:
            element.setEnabled(True)

        for element in self.treeWidgetInitialElements:
            element.setEnabled(False)



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

        vertex_id = vtk.vtkDoubleArray()
        vertex_id.SetNumberOfComponents(1)
        vertex_id.SetName("VertexID")

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
            vertex_id.InsertNextValue(2*i)
            vertex_id.InsertNextValue(2*i+1)
        print("Finished")  # Execution reaches here, error seems to be in cleanup upon closing

        graph.GetVertexData().AddArray(X)
        graph.GetVertexData().AddArray(Y)
        graph.GetEdgeData().AddArray(weights)
        graph.GetVertexData().AddArray(vertex_id)

        print("Added Data")
        layoutStrategy = vtk.vtkAssignCoordinatesLayoutStrategy()
        layoutStrategy.SetYCoordArrayName('Y')
        layoutStrategy.SetXCoordArrayName('X')

        self.graphWidget.viewer.update(graph)

    def displaySurfaces(self, progress_callback):
        """
        Create the VTK data structures and display a 3D surface based on the input image.

        :param (function) progress_callback:
            Function to emit progress signals
        """

        # Points coordinates structure
        triangle_vertices = vtk.vtkPoints()

        # associate the points to triangles
        triangle = vtk.vtkTriangle()
        trianglePointIds = triangle.GetPointIds()

        # put all triangles in an array
        triangles = vtk.vtkCellArray()

        surface_data = vtk.vtkIntArray()
        surface_data.SetNumberOfComponents(1)
        surface_data.SetName("SurfaceId")
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

        # Calculate the increment for each of the surfaces
        increment = 60.0/len(surf_list)

        for n, surf in enumerate(surf_list,1):
            print("Image-to-world coordinate trasformation ... %d" % surface)
            for point in surf:
                world_coord = numpy.dot(mTransform, point)
                triangle_vertices.InsertNextPoint(world_coord[0],
                                                  world_coord[1],
                                                  world_coord[2])

                # The id of the vertex of the triangle (0,1,2) is linked to
                # the id of the points in the list, so in facts we just link id-to-id
                trianglePointIds.SetId(isTriangle, point_count)
                isTriangle += 1
                point_count += 1

                if (isTriangle == 3):
                    isTriangle = 0
                    # insert the current triangle in the triangles array
                    triangles.InsertNextCell(triangle)
                    surface_data.InsertNextValue(surface)

            progress_callback.emit(int(n*increment + 30))
            surface += 1

        # polydata object
        trianglePolyData = vtk.vtkPolyData()
        trianglePolyData.SetPoints(triangle_vertices)
        trianglePolyData.SetPolys(triangles)
        trianglePolyData.GetCellData().AddArray(surface_data)


        self.viewer3DWidget.viewer.displayPolyData(trianglePolyData)

        actors = self.viewer3DWidget.viewer.actors

        if self.surfaceColourCheck.isChecked():
            # Change the colour of the polydata actors
            named_colours = vtk.vtkNamedColors()
            all_colours = named_colours.GetColorNames().split('\n')

            lut = vtk.vtkLookupTable()
            lut.SetNumberOfTableValues(surface)
            lut.Build()

            for i in range(surface):
                R,G,B = named_colours.GetColor3d(all_colours[i])
                lut.SetTableValue(i,R,G,B)


            actors[1][0].GetMapper().SetLookupTable(lut)
            actors[1][0].GetMapper().SetScalarRange(0, surface)
            actors[1][0].GetMapper().SetScalarModeToUseCellFieldData()
            actors[1][0].GetMapper().SelectColorArray('SurfaceId')
            actors[1][0].GetMapper().Update()

        self.viewer3DWidget.viewer.renWin.Render()

    def updateProgressBar(self, value):
        """
        Set progress bar percentage.

        :param (int) value:
            Integer value between 0-100.
        """

        self.progressBar.setValue(value)

    def completeProgressBar(self):
        """
        Set the progress bar to 100% complete and hide
        """
        self.progressBar.setValue(100)
        self.progressBar.hide()

    def showProgressBar(self):
        """
        Set the progress bar to 0% complete and show
        """
        self.progressBar.setValue(0)
        self.progressBar.show()

    def generateGraphTrigger(self):
        """
        Trigger method to allow threading of long running process
        """

        if self.graph_numpy_input_data is not None:
            self.showProgressBar()

            worker = Worker(self.generateGraph)
            self.threadpool.start(worker)

            # Progress bar signal handling
            worker.signals.finished.connect(self.completeProgressBar)
            worker.signals.progress.connect(self.updateProgressBar)

        else:
            msg = QtWidgets.QMessageBox(self.mainwindow)
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setWindowTitle("NO DATA")
            msg.setText("No data has been loaded into the reader. Please load a file to run the graph.")
            msg.exec_()


    def updateGraphTrigger(self):
        """
        Trigger method to allow threading of long running process
        """

        self.showProgressBar()

        worker = Worker(self.updateGraph)
        self.threadpool.start(worker)

        # Progress bar signal handling
        worker.signals.finished.connect(self.completeProgressBar)
        worker.signals.progress.connect(self.updateProgressBar)

    def openFileTrigger(self):
        """
        Trigger method to allow threading of long running process
        """

        self.showProgressBar()

        self.fn = QtWidgets.QFileDialog.getOpenFileNames(self.mainwindow, 'Open File')

        worker = Worker(self.openFile)
        self.threadpool.start(worker)

        # Progress bar signal handling
        worker.signals.progress.connect(self.updateProgressBar)
        worker.signals.finished.connect(self.completeProgressBar)
        worker.signals.error.connect(self.displayFileErrorDialog)


    def openFile(self, progress_callback=None, **kwargs):
        """
        Open file(s) based on results from QFileDialog

        :param (function) progress_callback:
            Callback funtion to emit progress percentage.
        """

        if 'filename' not in kwargs.keys():
            fn = self.fn
        else:
            fn = ([kwargs['filename']],)

        # If the user has pressed cancel, the first element of the tuple will be empty.
        # Quit the method cleanly
        if not fn[0]:
            return

        # Single file selection
        if len(fn[0]) == 1:
            file = fn[0][0]
            if progress_callback:
                progress_callback.emit(30)
            reader = vtk.vtkMetaImageReader()
            reader.AddObserver("ErrorEvent", self.e)
            reader.SetFileName(file)
            reader.Update()
            if progress_callback:
                progress_callback.emit(90)

        # Multiple TIFF files selected
        else:
            # Make sure that the files are sorted 0 - end
            filenames = natsorted(fn[0])
            increment = 30.0 / len(filenames)


            # Basic test for tiff images
            for n,file in enumerate(filenames,1):
                ftype = imghdr.what(file)
                if ftype != 'tiff':
                    # A non-TIFF file has been loaded, present error message and exit method
                    self.e('','','Problem reading file: {}'.format(file))
                    raise ReadError("File read error!")
                if progress_callback:
                    progress_callback.emit(int(n * increment))

            # Have passed basic test, can attempt to load
            numpy_image = Converter.pureTiff2Numpy(filenames=filenames, bounds=(256,256,256), progress_callback=progress_callback)
            reader = Converter.numpy2vtkImporter(numpy_image)
            reader.Update()

        if self.e.ErrorOccurred():
            raise ReadError()

        else:
            self.viewerWidget.viewer.setInput3DData(reader.GetOutput())
            self.viewer3DWidget.viewer.setInput3DData(reader.GetOutput())
            self.graph_numpy_input_data = Converter.vtk2numpy(reader.GetOutput(), transpose=[2,1,0])
            self.mainwindow.setStatusTip('Ready')
            self.spacing = reader.GetOutput().GetSpacing()
            self.origin = reader.GetOutput().GetOrigin()

            ### After successfully opening file, reset the interface ###
            # Reset linked state
            self.linkViewers(force_linked=True)

            # Reset graph if drawn
            self.graphWidget.viewer.update(vtk.vtkMutableDirectedGraph())

            # Reset graph parameter panel
            if self.hasDockableWindow:
                for element in self.treeWidgetInitialElements:
                    element.setEnabled(True)

                for element in self.treeWidgetUpdateElements:
                    element.setEnabled(False)

    def saveFile(self):
        dialog = QtWidgets.QFileDialog(self.mainwindow)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)

        fn = dialog.getSaveFileName(self.mainwindow,'Save As','.',"Images (*.png)")

        # Only save if the user has selected a name
        if fn[0]:
            self.viewerWidget.viewer.saveRender(fn[0])

    def close(self):
        QtWidgets.qApp.quit()

    def displayFileErrorDialog(self, tuple):
        exception_type, exception_object, traceback = tuple

        msg = QtWidgets.QMessageBox(self.mainwindow)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle("READ ERROR")
        msg.setText(repr(exception_object))
        msg.setDetailedText(self.e.ErrorMessage())
        msg.exec_()


def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Data viewer")
    parser.add_argument('--dev', dest='development', help='Specify file to open')
    args= parser.parse_args()
    print (args.development)

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    if args.development:
        ui.openFile(filename=args.development)
        ui.createDockableWindow()
        ui.generateGraphTrigger()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


