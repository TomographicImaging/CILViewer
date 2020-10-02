from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QThreadPool
from PyQt5.QtWidgets import QProgressDialog, QDialog, QLabel, QComboBox, QDialogButtonBox, QFormLayout, QWidget, QVBoxLayout, \
    QGroupBox, QLineEdit, QMessageBox, QPushButton
from functools import partial
import sys, os, time
from ccpi.viewer.QtThreading import Worker
import vtk

from ccpi.viewer.utils.conversion import cilBaseResampleReader

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



class WorkerWithProgressDialog(object):
    '''
    Creates a modal progress dialog and a worker to perform some task off the main ui thread.
    '''
    def __init__(self, parent, **kwargs):
        '''Creator

        Creates a default modal progress bar with close button enabled, maximise button disabled.
        If passed a function, with setAsyncTask, a thread will be created and launched but no 
        the signal to configure what happens on the thread finished is not connected.
        '''
        if parent is None:
            raise ValueError('Progress Dialog requires a parent. We were passed None')
        self._parent = parent

        self._labelText = "Progress"
        self._cancelButtonText = None
        self._onCancel = None
        self._min = 0
        self._max = 100
        self._windowFlags = [[QtCore.Qt.WindowCloseButtonHint, True],[QtCore.Qt.WindowMaximizeButtonHint, False]]
        self._title = ''
        self._windowModality = QtCore.Qt.ApplicationModal
    
    def setProgressDialogParameter(self, labelText=None, cancelButtonText=None, 
             pmin=None, pmax=None, 
             windowFlags=None, 
             title=None, windowModality=None, 
             onCancel = None):
        '''Defines the parameters for the progress dialog

        :param title: title on the progress bar dialog window
        :param labelText: label above the progress bar
        :param cancelButtonText: label on the optional cancel button. If None the Cancel button 
         will not appear
        :type cancelButtonText: str, default None
        :param onCancel: slot to attach to the signal cancel emitted by pressing the (optional) cancel button 
        :param pmin: minimum value of the progress bar, default 0
        :param pmax: maximum value of the progress bar, default 100
        :param windowFlags: Qt window flags, default close button enabled, maximise button disabled
        :param windowModality: window modality, default modal window

        Notice that the parent window of the progress dialog must be passed in the instantiation
        of the WorkerWithProgressDialog class.

        Also this method does not set any named parameter which has not been explicitly set.
        Default values are set in the creator of the class, this method will update the relevant 
        parameter only when passed.

        '''
        if labelText is not None:
            self._labelText = labelText
            self._modified = True
        if cancelButtonText is not None:
            self._cancelButtonText = cancelButtonText
            self._modified = True
        if onCancel is not None:
            self._onCancel = onCancel
            self._modified = True
        if pmin is not None:
            self._min = pmin
            self._modified = True
        if pmax is not None:
            self._max = pmax
            self._modified = True
        if windowFlags is not None:
            self._windowFlags = windowFlags
            self._modified = True
        if title is not None:
            self._title = title
            self._modified = True
        if windowModality is not None:
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
            # print ("modified")
            pd = QProgressDialog(self._labelText, self._cancelButtonText, self._min, self._max, 
                self._parent)
            pd.setWindowTitle(self._title)
            pd.setWindowModality(self._windowModality)
            # apply window flags
            for flag in self._windowFlags:
                pd.setWindowFlag(flag[0], flag[1])
            pd.setMinimumDuration(0.1)
            if self._cancelButtonText is not None:
                pd.cancel.connect(self._onCancel)
            self._progress_dialog = pd
            self.modified = False
        else:
            # print ("not modified")
            pd = self._progress_dialog
        return pd
    def setOnCancel(self, onCancel):
        '''connects the signal cancel of the progress dialog to the onCancel slot'''
        self._onCancel = onCancel
        self.modified = True
    
    def setAsyncTask(self, task, *args, **kwargs):
        '''Creates a Worker for the AsyncTask and attaches the 
        progress signal emitted by the Worker to the progress dialog'''
        print ("task ", task)
        w = Worker(task, *args, **kwargs)
        
        w.signals.progress.connect(self.progress)
        self._worker = w

    def progress(self,value = None):
        if value is not None:
            if int(value) > self.progress_dialog.value():
                self.progress_dialog.setValue(int(value))
    @property
    def worker(self):
        return self._worker
    @property
    def signals(self):
        '''QThreads signals are meant to be connected via this property
        
        instance = WorkerWithProgressDialog() 
        ...
        instance.signals.connect.finished(some_function)
        instance.signals.connect.progress(progress_function)
        '''
        return self.worker.signals   
        
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

#############################################################################
def asyncTask(N=10, form=None, progress_callback=None):
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
    if form is not None:
        print ("Press OK:\ndimensionality {}\n{}\ndtype {}, isBigEndian {}, F {}"\
             .format(form.dimensionality, form.shape , form.dtype, form.isBigEndian, form.isFortranOrder))
    i = 0
    while i < N:
        time.sleep(1)
        i+=1
        if progress_callback is not None:
            progress_callback.emit(i)
        else:
            print("progress_callback is None", i)


class cilGUIRawImageImporter(object):
    def __init__(self, parent):
        self._parent = parent
        self._fname = None
        
        pd = WorkerWithProgressDialog(parent = main)
        self.pd = pd
        
        pd.setProgressDialogParameters( labelText="labelText", cancelButtonText=None, 
                                        parent = main, title=title, pmax=N)
        
        dialog = ImportRawImageDialog(parent=main)
        self._dialog = dialog
        
        dialog.setTitle("Load Raw File")\
          .setOnFinished(
            lambda: self.threadpool.start(pd.worker)
        )

        self._vtkImage = vtk.vtkImageData()
         
        reader = cilBaseResampleReader()
        self._resamplereader = reader
        


    def setFileName(self, file_name):
        self._fname = os.path.abspath(file_name)
        self._dialog.setFileName(self._fname)

    @property
    def file_name(self):
        return self._fname
    def setThreadPool(self, value):
        self._threadpool = value
    @property
    def threadpool(self):
        if hasattr(self, "_threadpool"):
            return self._threadpool
        else:
            return QThreadPool.globalInstance()
    @property
    def dialog(self):
        return self._dialog

    def Update(self):
        self.dialog.update()

        self.dialog.setAsyncTask(asyncTask, N, dialog)

        dialog.show()


def test_progress_dialog():

    title = "title"
    N = 10
    pd = WorkerWithProgressDialog(parent = main)
    dialog = ImportRawImageDialog(parent=main)
    
    pd.setProgressDialogParameter(labelText="labelText", title=title, pmax=N)
    # if cancelButtonText is None then connecting to cancel is totally useless.
    # pd.setOnCancel(lambda: print ("Cancel dialog"))
    pd.setAsyncTask(asyncTask, N, dialog)

    threadpool = QThreadPool()
    # threadpool = QThreadPool.globalInstance()

    dialog.setFileName("pippo")\
        .setTitle("Hello!")\
        .setOnFinished(
            lambda: threadpool.start(pd.worker)
        )
    dialog.update()
    dialog.show()

def test_worker():
    
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
    if False:
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
        
        
        main.show()
    else:
        test_progress_dialog()
    sys.exit(app.exec())