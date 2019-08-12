import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
import vtk
#from ccpi.viewer.QVTKCILViewer import QVTKCILViewer
from ccpi.viewer.QVTKWidget import QVTKWidget
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from ccpi.viewer.CILViewer2D import CILViewer2D
from ccpi.viewer.utils import Converter
from natsort import natsorted
import imghdr
import os

class QVTKWidget2(QtWidgets.QFrame):
    '''A QFrame to embed in Qt application containing a VTK Render Window
    
    All the interaction is passed from Qt to VTK.

    :param viewer: The viewer you want to embed in Qt: CILViewer2D or CILViewer
    :param interactorStyle: The interactor style for the Viewer. 
    '''
    def __init__(self, viewer, **kwargs):
        '''Creator. Creates an instance of a QFrame and of a CILViewer
        
        The viewer is placed in the QFrame inside a QVBoxLayout. 
        The viewer is accessible as member 'viewer'
        '''
        super(QtWidgets.QFrame, self).__init__()
        self.vl = QtWidgets.QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.vl.addWidget(self.vtkWidget)
 
        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.viewer = viewer(renWin = self.vtkWidget.GetRenderWindow(),
                                iren = self.iren, 
                                ren = self.ren)
        # except KeyError:
        #     raise KeyError("Viewer class not provided. Submit an uninstantiated viewer class object"
        #                    "using 'viewer' keyword")
        
        

        if 'interactorStyle' in kwargs.keys():
            self.viewer.style = kwargs['interactorStyle'](self.viewer)
            self.viewer.iren.SetInteractorStyle(self.viewer.style)
        
        self.setLayout(self.vl)
    

def generateMetaImageHeader(datafname, typecode, shape, isFortran, isBigEndian, 
                        header_size=0, spacing=(1,1,1), origin=(0,0,0)):
    '''create MetaImageHeader for datafname based on the specifications in parameters'''
    # __typeDict = {'0':'MET_CHAR',    # VTK_SIGNED_CHAR,     # int8
    #               '1':'MET_UCHAR',   # VTK_UNSIGNED_CHAR,   # uint8
    #               '2':'MET_SHORT',   # VTK_SHORT,           # int16
    #               '3':'MET_USHORT',  # VTK_UNSIGNED_SHORT,  # uint16
    #               '4':'MET_INT',     # VTK_INT,             # int32
    #               '5':'MET_UINT',    # VTK_UNSIGNED_INT,    # uint32
    #               '6':'MET_FLOAT',   # VTK_FLOAT,           # float32
    #               '7':'MET_DOUBLE',  # VTK_DOUBLE,          # float64
    #       }
    __typeDict = ['MET_CHAR',    # VTK_SIGNED_CHAR,     # int8
                  'MET_UCHAR',   # VTK_UNSIGNED_CHAR,   # uint8
                  'MET_SHORT',   # VTK_SHORT,           # int16
                  'MET_USHORT',  # VTK_UNSIGNED_SHORT,  # uint16
                  'MET_INT',     # VTK_INT,             # int32
                  'MET_UINT',    # VTK_UNSIGNED_INT,    # uint32
                  'MET_FLOAT',   # VTK_FLOAT,           # float32
                  'MET_DOUBLE',  # VTK_DOUBLE,          # float64
    ]


    ar_type = __typeDict[typecode]
    # save header
    # minimal header structure
    # NDims = 3
    # DimSize = 181 217 181
    # ElementType = MET_UCHAR
    # ElementSpacing = 1.0 1.0 1.0
    # ElementByteOrderMSB = False
    # ElementDataFile = brainweb1.raw
    header = 'ObjectType = Image\n'
    header = ''
    header += 'NDims = {0}\n'.format(len(shape))
    if len(shape) == 2:
        header += 'DimSize = {} {}\n'.format(shape[0], shape[1])
        header += 'ElementSpacing = {} {}\n'.format(spacing[0], spacing[1])
        header += 'Position = {} {}\n'.format(origin[0], origin[1])
    
    elif len(shape) == 3:
        header += 'DimSize = {} {} {}\n'.format(shape[0], shape[1], shape[2])
        header += 'ElementSpacing = {} {} {}\n'.format(spacing[0], spacing[1], spacing[2])
        header += 'Position = {} {} {}\n'.format(origin[0], origin[1], origin[2])
    
    header += 'ElementType = {}\n'.format(ar_type)
    # MSB (aka big-endian)
    MSB = 'True' if isBigEndian else 'False'
    header += 'ElementByteOrderMSB = {}\n'.format(MSB)

    header += 'HeaderSize = {}\n'.format(header_size)
    header += 'ElementDataFile = {}'.format(os.path.basename(datafname))
    return header


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

        # a QFrame with a CILViewer inside
        self.vtkWidget = QVTKWidget(viewer=CILViewer2D)
        
        self.setCentralWidget(self.vtkWidget)

        self.toolbar()

        self.statusBar()
        self.setStatusTip('Open file to begin visualisation...')
        self.raw_import_dialog = None

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
        fn = QFileDialog.getOpenFileNames(self, 'Open File', 
        directory=os.path.abspath('C:/Users/ofn77899/Documents/Projects/collaborations/CatherineDisney'))

        # If the user has pressed cancel, the first element of the tuple will be empty.
        # Quit the method cleanly
        if not fn[0]:
            return

        # Single file selection
        if len(fn[0]) == 1:
            fname = fn[0][0]
            # base some decisions on the extension
            ff, fextension = os.path.splitext(os.path.basename(fname))

            if fextension in ['.mha', '.mhd']:
                # expects to read a MetaImage File
                reader = vtk.vtkMetaImageReader()
                reader.AddObserver("ErrorEvent", self.e)
                reader.SetFileName(fname)
                reader.Update()
            elif fextension in ['.raw']:
                # suppose we want to read in a binary file
                # popup a modal window asking for how to read it. 
                if self.raw_import_dialog is None:
                    self.raw_import_dialog = self.createRawImportDialog(fname)
                dialog = self.raw_import_dialog['dialog']
                
                dialog.exec_()
                return


        # Multiple TIFF files selected
        else:
            # Make sure that the files are sorted 0 - end
            filenames = natsorted(fn[0])

            # Basic test for tiff images
            for fname in filenames:
                ftype = imghdr.what(fname)
                if ftype != 'tiff':
                    # A non-TIFF file has been loaded, present error message and exit method
                    self.e('','','When reading multiple files, all files must TIFF formatted.')
                    fname = fname
                    self.displayFileErrorDialog(fname)
                    return

            # Have passed basic test, can attempt to load
            #numpy_image = Converter.tiffStack2numpyEnforceBounds(filenames=filenames)
            #reader = Converter.numpy2vtkImporter(numpy_image)
            #reader.Update()
            reader = vtk.vtkTIFFReader()
            sa = vtk.vtkStringArray()
            #i = 0
            #while (i < 1054):
            for fname in filenames:
                #fname = os.path.join(directory,"8bit-1%04d.tif" % i)
                i = sa.InsertNextValue(fname)
                
            print ("read {} files".format( i ))
            
            reader.SetFileNames(sa)
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

    def generateUIFormView(self):
        '''creates a widget with a form layout group to add things to

        basically you can add widget to the returned groupBoxFormLayout and paramsGroupBox
        The returned dockWidget must be added with
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dockWidget)
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
    def createRawImportDialog(self, fname):
        dialog = QDialog(self)
        ui = self.generateUIFormView()
        groupBox = ui['groupBox']
        formLayout = ui['groupBoxFormLayout']
        widgetno = 1
        
        # dimensionality
        dimensionalityLabel = QLabel(groupBox)
        dimensionalityLabel.setText("Dimensionality")
        formLayout.setWidget(widgetno, QFormLayout.LabelRole, dimensionalityLabel)
        dimensionalityValue = QComboBox(groupBox)
        dimensionalityValue.addItem("3D")
        dimensionalityValue.addItem("2D")
        dimensionalityValue.setCurrentIndex(0)
        # dimensionalityValue.currentIndexChanged.connect(lambda: \
        #             self.overlapZValueEntry.setEnabled(True) \
        #             if self.dimensionalityValue.currentIndex() == 0 else \
        #             self.overlapZValueEntry.setEnabled(False))
        
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
        dtypeValue.addItem("int8")
        dtypeValue.addItem("uint8")
        dtypeValue.addItem("int16")
        dtypeValue.addItem("uint16")
        dtypeValue.addItem("int32")
        dtypeValue.addItem("uint32")
        dtypeValue.addItem("float32")
        dtypeValue.addItem("float64")
        dtypeValue.setCurrentIndex(0)
        # dimensionalityValue.currentIndexChanged.connect(lambda: \
        #             self.overlapZValueEntry.setEnabled(True) \
        #             if self.dimensionalityValue.currentIndex() == 0 else \
        #             self.overlapZValueEntry.setEnabled(False))
        
        formLayout.setWidget(widgetno, QFormLayout.FieldRole, dtypeValue)
        widgetno += 1

        # Endiannes
        endiannesLabel = QLabel(groupBox)
        endiannesLabel.setText("Byte Ordering")
        formLayout.setWidget(widgetno, QFormLayout.LabelRole, endiannesLabel)
        endiannes = QComboBox(groupBox)
        endiannes.addItem("Big Endian")
        endiannes.addItem("Little Endian")
        endiannes.setCurrentIndex(1)
        # dimensionalityValue.currentIndexChanged.connect(lambda: \
        #             self.overlapZValueEntry.setEnabled(True) \
        #             if self.dimensionalityValue.currentIndex() == 0 else \
        #             self.overlapZValueEntry.setEnabled(False))
        
        formLayout.setWidget(widgetno, QFormLayout.FieldRole, endiannes)
        widgetno += 1

        # Fortran Ordering
        fortranLabel = QLabel(groupBox)
        fortranLabel.setText("Fortran Ordering")
        formLayout.setWidget(widgetno, QFormLayout.LabelRole, fortranLabel)
        fortranOrder = QComboBox(groupBox)
        fortranOrder.addItem("Fortran Order: XYZ")
        fortranOrder.addItem("C Order: ZYX")
        fortranOrder.setCurrentIndex(1)
        # dimensionalityValue.currentIndexChanged.connect(lambda: \
        #             self.overlapZValueEntry.setEnabled(True) \
        #             if self.dimensionalityValue.currentIndex() == 0 else \
        #             self.overlapZValueEntry.setEnabled(False))
        
        formLayout.setWidget(widgetno, QFormLayout.FieldRole, fortranOrder)
        widgetno += 1

        buttonbox = QDialogButtonBox(QDialogButtonBox.Ok |
                                    QDialogButtonBox.Cancel)
        buttonbox.accepted.connect(lambda: self.saveMetaImageHeaderAndLoad(fname))
        buttonbox.rejected.connect(dialog.close)
        formLayout.addWidget(buttonbox)

        dialog.setLayout(ui['verticalLayout'])
        dialog.setModal(True)

        return {'dialog': dialog, 'ui': ui, 
                'dimensionality': dimensionalityValue, 
                'dimX': dimXValueEntry, 'dimY': dimYValueEntry, 'dimZ': dimZValueEntry,
                'dtype': dtypeValue, 'endiannes' : endiannes, 'isFortran' : fortranOrder,
                'buttonBox': buttonbox}
    def saveMetaImageHeaderAndLoad(self, fname):
        print ("File Name", fname)
        print ('Dimensionality', self.raw_import_dialog['dimensionality'].currentIndex())
        dimensionality = [3,2][self.raw_import_dialog['dimensionality'].currentIndex()]
        dimX = int ( self.raw_import_dialog['dimX'].text() )
        dimY = int ( self.raw_import_dialog['dimY'].text() )
        isFortran = True if self.raw_import_dialog['isFortran'].currentIndex() == 0 else False
        if isFortran:
            shape = (dimX, dimY)
        else:
            shape = (dimY, dimX)
        if dimensionality == 3:
            dimZ = int ( self.raw_import_dialog['dimZ'].text() )
            if isFortran:
                shape = (dimX, dimY, dimZ)
            else:
                shape = (dimZ, dimY, dimX)
        
        isBigEndian = True if self.raw_import_dialog['endiannes'].currentIndex() == 0 else False
        typecode = self.raw_import_dialog['dtype'].currentIndex()

        # basic sanity check
        file_size = os.stat(fname).st_size

        expected_size = 1
        for el in shape:
            expected_size *= el
            
        if typecode in [0,1]:
            mul = 1
        elif typecode in [2,3]:
            mul = 2
        elif typecode in [4,5,6]:
            mul = 4
        else:
            mul = 8
        expected_size *= mul
        if file_size != expected_size:
            self.warningDialog(
                detailed_text='Expected Data size: {}b\nFile Data size:     {}b\n'.format(expected_size, file_size),
                window_title='File Size Error',
                message='Expected Data Size does not match File size.')
            self.raw_import_dialog['dialog'].close()
            return

        header = generateMetaImageHeader(fname, typecode, shape, isFortran, isBigEndian, 
                        header_size=0, spacing=(1,1,1), origin=(0,0,0))

        
        
        print (header)
        ff, fextension = os.path.splitext(os.path.basename(fname))
        hdrfname = os.path.join(os.path.dirname(fname),  ff + '.mhd' )
        with open(hdrfname , 'w') as hdr:
            hdr.write(header)
        self.raw_import_dialog['dialog'].close()
        # expects to read a MetaImage File
        reader = vtk.vtkMetaImageReader()
        reader.AddObserver("ErrorEvent", self.e)
        reader.SetFileName(hdrfname)
        reader.Update()
        if self.e.ErrorOccurred():
            self.displayFileErrorDialog(hdrfname)
        else:
            self.vtkWidget.viewer.setInput3DData(reader.GetOutput())

        self.setStatusTip('Ready')

    def warningDialog(self, message='', window_title='', detailed_text=''):
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Information)
        dialog.setText(message)
        dialog.setWindowTitle(window_title)
        dialog.setDetailedText(detailed_text)
        dialog.setStandardButtons(QMessageBox.Ok)
        retval = dialog.exec_()
        return retval
        
def main():
    err = vtk.vtkFileOutputWindow()
    err.SetFileName("viewer.log")
    vtk.vtkOutputWindow.SetInstance(err)
    
    App = QApplication(sys.argv)
    gui = Window()
    sys.exit(App.exec_())

if __name__=="__main__":
    main()