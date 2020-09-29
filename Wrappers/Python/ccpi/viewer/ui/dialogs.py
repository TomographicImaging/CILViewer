from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QThreadPool
from PyQt5.QtWidgets import QProgressDialog, QDialog, QLabel, QComboBox, QDialogButtonBox, QFormLayout, QWidget, QVBoxLayout, QGroupBox, QLineEdit, QMessageBox
# from ccpi.viewer.io import generateUIFormView
from functools import partial
import sys, os
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


def createRawImportDialog(main_window, fname, output_image, info_var, resample, target_size, crop_image, origin, target_z_extent, finish_fn):
        dialog = QDialog(main_window)
        ui = generateUIFormView()
        groupBox = ui['groupBox']
        formLayout = ui['groupBoxFormLayout']
        widgetno = 1

        title = "Config for " + os.path.basename(fname)
        dialog.setWindowTitle(title)
        
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
        # dimensionalityValue.currentIndexChanged.connect(lambda: \
        #             main_window.overlapZValueEntry.setEnabled(True) \
        #             if main_window.dimensionalityValue.currentIndex() == 0 else \
        #             main_window.overlapZValueEntry.setEnabled(False))
        
        formLayout.setWidget(widgetno, QFormLayout.FieldRole, fortranOrder)
        widgetno += 1

        buttonbox = QDialogButtonBox(QDialogButtonBox.Ok |
                                    QDialogButtonBox.Cancel)
        buttonbox.accepted.connect(lambda: createConvertRawImageWorker(main_window,fname, output_image, info_var, resample, target_size,
                                                                       crop_image, origin, target_z_extent, finish_fn))
        buttonbox.rejected.connect(dialog.close)
        formLayout.addWidget(buttonbox)

        dialog.setLayout(ui['verticalLayout'])
        dialog.setModal(True)

        return {'dialog': dialog, 'ui': ui, 
                'dimensionality': dimensionalityValue, 
                'dimX': dimXValueEntry, 'dimY': dimYValueEntry, 'dimZ': dimZValueEntry,
                'dtype': dtypeValue, 'endiannes' : endiannes, 'isFortran' : fortranOrder,
                'buttonBox': buttonbox}

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main = QtWidgets.QMainWindow()
    def onFinished(self):
        print ("Press OK:\ndimensionality {}\n{}\ndtype {}, isBigEndian {}, F {}"\
             .format(self.dimensionality, self.shape , self.dtype, self.isBigEndian, self.isFortranOrder)
            #  , self.dtype, self.isBigEndian, self.isFortranOrder )
        )
        
    dialog = ImportRawImageDialog(parent=main)
    dialog.setFileName("pippo")\
        .setTitle("Hello!")\
        .setOnFinished(
            partial(lambda: onFinished(dialog))
        )
    dialog.update()
    
    dialog.show()

    
    sys.exit(app.exec_())