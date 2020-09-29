from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QThreadPool
from PyQt5.QtWidgets import QProgressDialog, QDialog, QLabel, QComboBox, QDialogButtonBox, QFormLayout, QWidget, QVBoxLayout, \
    QGroupBox, QLineEdit, QMessageBox, QPushButton
# from ccpi.viewer.io import generateUIFormView
from functools import partial
import sys, os, time
from ccpi.viewer.QtThreading import Worker

def generateUIFormView():
    '''creates a widget with a form layout group to add things to

    basically you can add widget to the returned groupBoxFormLayout and paramsGroupBox
    The returned dockWidget must be added with
    main_window.addDockWidget(QtCore.Qt.RightDockWidgetArea, dockWidget)
    '''
    dockWidgetContents = QWidget()


    # Add vertical layout to dock contents
    dockContentsVerticalLayout = QVBoxLayout(dockWidgetContents)
    dockContentsVerticalLayout.setContentsMargins(0, 0, 0, 0)

    # Create widget for dock contents
    internalDockWidget = QWidget(dockWidgetContents)

    # Add vertical layout to dock widget
    internalWidgetVerticalLayout = QVBoxLayout(internalDockWidget)
    internalWidgetVerticalLayout.setContentsMargins(0, 0, 0, 0)

    # Add group box
    paramsGroupBox = QGroupBox(internalDockWidget)


    # Add form layout to group box
    groupBoxFormLayout = QFormLayout(paramsGroupBox)

    # Add elements to layout
    internalWidgetVerticalLayout.addWidget(paramsGroupBox)
    dockContentsVerticalLayout.addWidget(internalDockWidget)
    #dockWidget.setWidget(dockWidgetContents)
    return {'widget': dockWidgetContents,
            'verticalLayout':dockContentsVerticalLayout, 
            'internalWidget': internalDockWidget,
            'internalVerticalLayout': internalWidgetVerticalLayout, 
            'groupBox' : paramsGroupBox,
            'groupBoxFormLayout': groupBoxFormLayout}


def createProgressWindow(main_window, title, text, max = 100, cancel = None):
    main_window.progress_window = QProgressDialog(text, "Cancel", 0,max, main_window, QtCore.Qt.Window) 
    main_window.progress_window.setWindowTitle(title)
    main_window.progress_window.setWindowModality(QtCore.Qt.ApplicationModal) #This means the other windows can't be used while this is open
    main_window.progress_window.setMinimumDuration(0.1)
    main_window.progress_window.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
    main_window.progress_window.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, False)
    if cancel is None:
        main_window.progress_window.setCancelButton(None)
    else:
        main_window.progress_window.canceled.connect(cancel)

class WorkerWithProgressDialog(object):
    '''
    Creates a modal progress dialog and a worker to perform some task off the main ui thread.
    '''
    def __init__(self, parent):
        self._parent = None
        self._cancelButtonText = "Cancel"
        self._labelText = None
        self._min = 0 
        self._max = 100
        self._modified = True
    
    def setProgressDialogParameters(self, labelText="", cancelButtonText="Cancel", 
             pmin=0, pmax=100, parent=None, 
             windowFlags=[[QtCore.Qt.WindowCloseButtonHint, True],[QtCore.Qt.WindowMaximizeButtonHint, False]], 
             title="", windowModality=QtCore.Qt.ApplicationModal):
        self._labelText = labelText
        self._cancelButtonText = cancelButtonText
        self._min = pmin
        self._max = pmax
        self._parent = parent
        self._windowFlags = windowFlags
        self._title = title
        self._windowModality = windowModality
        self._modified = True
    @property
    def modified(self):
        return self._modified
    @modified.setter
    def modified(self, value):
        self._modified = value
    @property
    def progress_dialog(self):
        if self.modified:
            print ("modified")
            pd = QProgressDialog(self._labelText, self._cancelButtonText, self._min, self._max, 
                self._parent)
            pd.setWindowTitle(self._title)
            pd.setWindowModality(self._windowModality)
            # apply window flags
            for flag in self._windowFlags:
                pd.setWindowFlag(flag[0], flag[1])
            pd.setMinimumDuration(0.1)
            self._progress_dialog = pd
            self.modified = False
        else:
            print ("not modified")
            pd = self._progress_dialog
        return pd
    def setOnCancelled(self, onCancel):
        pd = self.progress_dialog
        # button = QPushButton("Cancel")
        # pd.setCancelButton(button)
        pd.canceled.connect(onCancel)
    def setAsyncTask(self, task, *args, **kwargs):
        work = Worker(task, *args, **kwargs)


    def setParentWindow(self, parent):
        self._parent = parent
    @property
    def parent(self):
        return self._parent
    
    def __call__(self):
        print ("Call ", self.__class__.__name__)
    

class ImportRawImageDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self._ui = generateUIFormView()
        self._fname           = None
        self._outdata         = None
        self._info_var        = None
        self._resample        = None
        self._target_size     = None
        self._crop_image      = None
        self._origin          = None
        self._target_z_extent = None
        self._on_finished     = None


    def setFileName(self, value):
        self._fname = value
        return self
    @property
    def fileName(self):
        return self._fname

    @property
    def title(self):
        return self._title
    def setTitle(self, value):
        self._title = value
        return self
    
    def setOutputImage(self, data):
        self._outdata = data
        return self
    @property
    def outputImage(self):
        return self._outdata

    def setInfoVar(self, info_var):
        self._info_var = info_var
        return self
    @property
    def infoVar(self):
        return self._info_var

    def setResample(self, value):
        self._resample = value
        return self
    @property
    def resample(self):
        return self._resample

    def setTargetSize(self, value):
        self._target_size = value
        return self
    @property
    def targetSize(self):
        return self._target_size

    def setCropImage(self, value):
        self._crop_image = value
        return self
    @property
    def cropImage(self):
        return self._crop_image

    def setOrigin(self, value):
        self._origin = value
        return self
    @property
    def origin(self):
        return self._origin

    def setTargetZExtent(self, value):
        self._target_z_extent = value
        return self
    @property
    def targetZExtent(self):
        return self._target_z_extent

    def setOnFinished(self, function):
        self._on_finished = function
        return self
    @property
    def onFinished(self):
        return self._on_finished

    #def setupRawImportDialog( main_window, fname, output_image, info_var, resample, target_size, crop_image, origin, target_z_extent, finish_fn):
    #def createRawImportDialog(main_window, fname, output_image, info_var, resample, target_size, crop_image, origin, target_z_extent, finish_fn):
        # dialog = QDialog(main_window)
    def update(self):
        ui = self._ui
        groupBox = ui['groupBox']
        formLayout = ui['groupBoxFormLayout']
        widgetno = 1

        title = "Config for " + os.path.basename(self.fileName)
        self.setWindowTitle(self.title)
        
        # dimensionality
        dimensionalityLabel = QLabel(groupBox)
        dimensionalityLabel.setText("Dimensionality")
        formLayout.setWidget(widgetno, QFormLayout.LabelRole, dimensionalityLabel)
        dimensionalityValue = QComboBox(groupBox)
        dimensionalityValue.addItem("3D")
        dimensionalityValue.addItem("2D")
        dimensionalityValue.setCurrentIndex(0)
        # dimensionalityValue.currentIndexChanged.connect(lambda: \
        #             main_window.overlapZValueEntry.setEnabled(True) \
        #             if main_window.dimensionalityValue.currentIndex() == 0 else \
        #             main_window.overlapZValueEntry.setEnabled(False))
        
        formLayout.setWidget(widgetno, QFormLayout.FieldRole, dimensionalityValue)
        widgetno += 1

        validator = QtGui.QIntValidator()
        # Add X size
        dimXLabel = QLabel(groupBox)
        dimXLabel.setText("Size X")
        formLayout.setWidget(widgetno, QFormLayout.LabelRole, dimXLabel)
        dimXValueEntry = QLineEdit(groupBox)
        dimXValueEntry.setValidator(validator)
        dimXValueEntry.setText("0")
        formLayout.setWidget(widgetno, QFormLayout.FieldRole, dimXValueEntry)
        widgetno += 1

        # Add Y size
        dimYLabel = QLabel(groupBox)
        dimYLabel.setText("Size Y")
        formLayout.setWidget(widgetno, QFormLayout.LabelRole, dimYLabel)
        dimYValueEntry = QLineEdit(groupBox)
        dimYValueEntry.setValidator(validator)
        dimYValueEntry.setText("0")
        formLayout.setWidget(widgetno, QFormLayout.FieldRole, dimYValueEntry)
        widgetno += 1
        
        # Add Z size
        dimZLabel = QLabel(groupBox)
        dimZLabel.setText("Size Z")
        formLayout.setWidget(widgetno, QFormLayout.LabelRole, dimZLabel)
        dimZValueEntry = QLineEdit(groupBox)
        dimZValueEntry.setValidator(validator)
        dimZValueEntry.setText("0")
        formLayout.setWidget(widgetno, QFormLayout.FieldRole, dimZValueEntry)
        widgetno += 1
        
        # Data Type
        dtypeLabel = QLabel(groupBox)
        dtypeLabel.setText("Data Type")
        formLayout.setWidget(widgetno, QFormLayout.LabelRole, dtypeLabel)
        dtypeValue = QComboBox(groupBox)
        dtypeValue.addItems(["uint8", "int8", "uint16", "int16", "uint32", "int32", "float32", "float64"])
        dtypeValue.setCurrentIndex(0)
        
        formLayout.setWidget(widgetno, QFormLayout.FieldRole, dtypeValue)
        widgetno += 1

        # Endiannes
        endiannesLabel = QLabel(groupBox)
        endiannesLabel.setText("Byte Ordering")
        formLayout.setWidget(widgetno, QFormLayout.LabelRole, endiannesLabel)
        endiannes = QComboBox(groupBox)
        endiannes.addItems(["Big Endian","Little Endian"])
        endiannes.setCurrentIndex(1)
        
        formLayout.setWidget(widgetno, QFormLayout.FieldRole, endiannes)
        widgetno += 1

        # Fortran Ordering
        fortranLabel = QLabel(groupBox)
        fortranLabel.setText("Fortran Ordering")
        formLayout.setWidget(widgetno, QFormLayout.LabelRole, fortranLabel)
        fortranOrder = QComboBox(groupBox)
        fortranOrder.addItem("Fortran Order: XYZ")
        fortranOrder.addItem("C Order: ZYX")
        fortranOrder.setCurrentIndex(0)
        
        formLayout.setWidget(widgetno, QFormLayout.FieldRole, fortranOrder)
        widgetno += 1

        buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonbox.accepted.connect(self.onFinished)
        # buttonbox.accepted.connect(
        #     lambda: createConvertRawImageWorker(self.parent, 
        #                                         self.getFileName(), 
        #                                         self.getOutputImage(), 
        #                                         self.getInfoVar(), 
        #                                         self.getResample(), 
        #                                         self.getTargetSize(),
        #                                         self.getCropImage(), 
        #                                         self.getOrigin(), 
        #                                         self.getTargetZExtent(), 
        #                                         self.getOnFinished())
        # )
        buttonbox.rejected.connect(self.close)
        formLayout.addWidget(buttonbox)

        self.setLayout(ui['verticalLayout'])
        self.setModal(True)

        self.form = { 
                'dimensionality': dimensionalityValue, 
                'dimX': dimXValueEntry, 'dimY': dimYValueEntry, 'dimZ': dimZValueEntry,
                'dtype': dtypeValue, 'endiannes' : endiannes, 'isFortran' : fortranOrder,
                'buttonBox': buttonbox}
        
    @property
    def dimensionality(self):
        return 3 if self.form['dimensionality'].currentIndex() == 0 else 2
    @property
    def dimX(self):
        return int(self.form['dimX'].text())
    @property
    def dimY(self):
        return int(self.form['dimY'].text())
    @property
    def dimZ(self):
        if self.dimensionality == 2:
            raise ValueError('Dimensionality is 2, so dimZ does not have sense')
        return int(self.form['dimZ'].text())
    @property
    def shape(self):
        try:
            return (self.dimX, self.dimY, self.dimZ)
        except ValueError as ve:
            return (self.dimX, self.dimY)
    @property
    def dtype(self):
        print ("dtype")
        return self.form['dtype'].currentText()
    def getDType(self):
        return self.form['dtype'].currentText()
    @property
    def isBigEndian(self):
        return True if self.form['endiannes'].currentIndex() == 0 else False
    @property
    def isFortranOrder(self):
        return True if self.form['isFortran'].currentIndex() == 0 else False




def test_progress_dialog():
    app = QtWidgets.QApplication(sys.argv)
    main = QtWidgets.QMainWindow()
    
    def onFinished(self):
        print ("Press OK:\ndimensionality {}\n{}\ndtype {}, isBigEndian {}, F {}"\
             .format(self.dimensionality, self.shape , self.dtype, self.isBigEndian, self.isFortranOrder)
            #  , self.dtype, self.isBigEndian, self.isFortranOrder )
        )

    def launchProgressDialog(parent, labelText, title, cancelButtonText="Cancel", asyncTask=None):
        pd = WorkerWithProgressDialog(parent = parent)
        pd.setProgressDialogParameters(labelText="labelText", cancelButtonText="Cancel", 
            parent = main, title=title)
        pd.setMinimumDuration(0.001)
        pd.setOnCancelled(lambda: print ("this is a lambda"))

    dialog = ImportRawImageDialog(parent=main)
    dialog.setFileName("pippo")\
        .setTitle("Hello!")\
        .setOnFinished(
            #partial(lambda: onFinished(dialog))
            partial(lambda: launchProgressDialog(main))
        )
    dialog.update()
    
    dialog.show()
    
    sys.exit(app.exec_())

def test_worker():
    def asyncTask(N=10, progress_callback=None):
        '''an example of an async task
        
        :param N: integer number of loops
        :param progress_callback: callback that emits the current progress. 
          If passed to the Worker class, the progress_callback is defined 
          internally in the Worker class and the user is supposed just to 
          connect the Worker signal progress with a function that receives 
          the current progress as an integer, e.g.

          
          work = Worker(asyncTask, 4)
          work.signals.progress.connect(lambda x: print("progress.connect", x))
        '''
        # N=10
        i = 0
        while i < N:
            time.sleep(1)
            if progress_callback is not None:
                progress_callback.emit(i)
            else:
                print("progress_callback is None", i)
            i+=1
    def asyncTaskSimple():
        N = 2
        i = 0
        while i < N:
            time.sleep(1)
            i+=1
    
    work = Worker(asyncTask, 4)
    work.signals.progress.connect(lambda x: print("progress.connect", x))
    work.signals.result.connect(lambda: print("Done!"))
    return work
    
if __name__ == "__main__":
    
    app = QtWidgets.QApplication(sys.argv)
    main = QtWidgets.QMainWindow()
    print ("creating Workers")
    work0 = test_worker()
    work1 = test_worker()
    print ("creating QThreadPool")
    threadpool = QThreadPool()
    print ("Starting workers")
    threadpool.start(work0)
    time.sleep(1)
    threadpool.start(work1)
    print ("End")
    #test_progress_dialog()
    
    main.show()
    sys.exit(app.exec())