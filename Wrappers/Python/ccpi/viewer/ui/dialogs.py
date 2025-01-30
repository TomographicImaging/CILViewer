import os
import h5py
from eqt.ui import FormDialog
from eqt.ui.SessionDialogs import AppSettingsDialog, ErrorDialog
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtWidgets import QCheckBox, QDoubleSpinBox, QLabel, QLineEdit, QComboBox
import numpy as np
from ccpi.viewer.utils import Converter
from ccpi.viewer.utils.conversion import cilRawCroppedReader
from ccpi.viewer.QCILViewerWidget import QCILViewerWidget
from ccpi.viewer.CILViewer2D import CILViewer2D as viewer2D
import numpy as np
import vtk
from functools import reduce
import tempfile
import logging


class ViewerSettingsDialog(AppSettingsDialog):
    ''' This is a dialog window which allows the user to set:
    - maximum size to downsample images to for display
    - Whether to use GPU for volume rendering
    '''

    def __init__(self, parent):
        super(ViewerSettingsDialog, self).__init__(parent)

        self._addViewerSettingsWidgets()

    def _addViewerSettingsWidgets(self):
        self.formWidget.addSeparator('viewer_settings_separator')

        self.formWidget.addTitle(QLabel("Viewer Settings"), "viewer_settings_title")

        vis_size = QLabel("Maximum downsampled image size (GB): ")
        vis_size_entry = QDoubleSpinBox()
        vis_size_entry.setMaximum(64.0)
        vis_size_entry.setMinimum(0.01)
        vis_size_entry.setSingleStep(0.01)

        self.addWidget(vis_size_entry, vis_size, 'vis_size')

        self.formWidget.addSeparator('adv_separator')

        self.formWidget.addTitle(QLabel("Advanced Settings"), 'adv_settings_title')

        gpu_checkbox = QCheckBox("Use GPU for volume render. (Recommended) ")

        self.addSpanningWidget(gpu_checkbox, 'gpu_checkbox')

        # self.formWidget.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        # self.formWidget.uiElements['verticalLayout'].setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        # self.formWidget.uiElements['groupBox'].setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        # self.formWidget.uiElements['groupBoxFormLayout'].setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)


class RawInputDialog(FormDialog):
    '''
    This is a dialog window which allows the user to set information
    for a raw file, including:
    - dimensionality
    - size of dimensions
    - data type
    - endianness
    - fortran ordering

    The dialog can let the user preview the data and verify that it is correct.

    Example:
    --------

    One can instantiate this dialog and reduce the supported types by overriding the 
    default supported_types with setSupportedTypes:

    >>> dialog = RawInputDialog(parent, fname)
    >>> dialog.setSupportedTypes(['float32', 'float64'])

    '''

    supported_types = [np.dtype(f) for f in Converter.dtype_name_to_vtkType.keys()]

    def __init__(self, parent, fname):
        super(RawInputDialog, self).__init__(parent, fname)
        self.setFileName(fname)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        fw = self.formWidget

        # dimensionality:
        dimensionalityLabel = QLabel("Dimensionality")
        dimensionalityValue = QComboBox()
        dimensionalityValue.addItems(["3D", "2D"])
        dimensionalityValue.setCurrentIndex(0)
        fw.addWidget(dimensionalityValue, dimensionalityLabel, "dimensionality")

        validator = QtGui.QIntValidator()
        validator.setBottom(0)
        # Entry for size of dimensions:
        for dim in ['Width', 'Height', 'Images']:
            ValueEntry = QLineEdit()
            ValueEntry.setValidator(validator)
            ValueEntry.setText("0")
            Label = QLabel("{}".format(dim))
            fw.addWidget(ValueEntry, Label, 'dim_{}'.format(dim))

        dimensionalityValue.currentIndexChanged.connect(self.enableDisableDimZ)

        # Data Type
        self.supported_types = RawInputDialog.supported_types.copy()
        dtypeLabel = QLabel("Data Type")
        dtypeValue = QComboBox()
        dtypeValue.addItems([dt.name for dt in self.supported_types])
        dtypeValue.setCurrentIndex(1)
        fw.addWidget(dtypeValue, dtypeLabel, 'dtype')

        # Endianness
        endiannesLabel = QLabel("Byte Ordering")
        endiannes = QComboBox()
        endiannes.addItems(["Big Endian", "Little Endian"])
        endiannes.setCurrentIndex(0)
        fw.addWidget(endiannes, endiannesLabel, 'endianness')

        # Fortran Ordering
        fortranLabel = QLabel("Data Ordering")
        fortranOrder = QComboBox()
        fortranOrder.addItems(["Width-Height-Images", "Images-Height-Width"])
        fortranOrder.setCurrentIndex(0)
        fw.addWidget(fortranOrder, fortranLabel, "is_fortran")

        previewSliceLabel = QLabel("Preview:")
        previewSliceEntry = QLineEdit()
        previewSliceEntry.setValidator(validator)
        previewSliceEntry.setText("0")

        fw.addWidget(previewSliceEntry, previewSliceLabel, "preview_slice")

        # preview button
        previewButton = QtWidgets.QPushButton("Preview")
        fw.addWidget(previewButton, "", "preview_button")
        self.preview_open = False
        previewButton.clicked.connect(self.preview)

        self.setLayout(fw.uiElements['verticalLayout'])

        self.Cancel.clicked.connect(self.close)

    def setFileName(self, filename):
        '''Set the filename used in the dialog and the dialog title.'''
        self.fname = os.path.abspath(filename)
        title = "Config for " + os.path.basename(filename)
        self.setWindowTitle(title)

    def setSupportedTypes(self, types):
        '''Updates the list of supported types
        
        Parameters:
        -----------
            types: list 
              list of dtypes accepted by numpy.dtype
        '''
        self.supported_types = types
        self.getWidget('dtype').clear()
        self.getWidget('dtype').addItems([dt.name for dt in self.supported_types])

    def getRawAttrs(self):
        '''
        Returns a dictionary containing the raw attributes:
        - shape
        - is_fortran
        - is_big_endian
        - typecode
        '''
        raw_attrs = {}
        widgets = self.formWidget.widgets
        dimensionality = [3, 2][widgets['dimensionality_field'].currentIndex()]
        dims = []
        dims.append(int(widgets['dim_Width_field'].text()))
        dims.append(int(widgets['dim_Height_field'].text()))
        if dimensionality == 3:
            dims.append(int(widgets['dim_Images_field'].text()))

        raw_attrs['shape'] = dims
        raw_attrs['is_fortran'] = not bool(widgets['is_fortran_field'].currentIndex())
        # raw_attrs['is_fortran'] = False
        raw_attrs['is_big_endian'] = not bool(widgets['endianness_field'].currentIndex())
        raw_attrs['typecode'] = widgets['dtype_field'].currentText()
        raw_attrs['preview_slice'] = int(widgets['preview_slice_field'].text())

        return raw_attrs

    def enableDisableDimZ(self):
        '''
        Enables or disables the Z dimension entry based on the dimensionality
        '''
        widgets = self.formWidget.widgets
        dimensionality = [3, 2][widgets['dimensionality_field'].currentIndex()]
        if dimensionality == 3:
            widgets['dim_Images_field'].setEnabled(True)
        else:
            widgets['dim_Images_field'].setEnabled(False)

    def preview(self):
        pars = self.getRawAttrs()

        # retrieve info about image file from interface
        dimensionality = [3, 2][self.getWidget('dimensionality').currentIndex()]
        dimX, dimY, dimZ = pars['shape']
        isFortran = pars['is_fortran']
        isBigEndian = pars['is_big_endian']
        # typecode = pars['typecode']
        typecode = self.getWidget('dtype').currentText()

        shape = (dimX, dimY)
        if dimensionality == 3:
            shape = (dimX, dimY, dimZ)

        # Construct a data type
        dt = np.dtype(typecode)

        if isBigEndian:
            dt_txt = ">"  # big endian
        else:
            dt_txt = "<"
        dt = dt.newbyteorder(dt_txt)

        bytes_per_element = dt.itemsize

        # basic sanity check
        file_size = os.stat(self.fname).st_size

        expected_size = reduce(lambda x, y: x * y, shape, 1) * bytes_per_element

        if file_size < expected_size:
            errors = {"type": "size", "file_size": file_size, "expected_size": expected_size}
            dmsg = f'The file size is smaller than expected.\nThe file size is {file_size} bytes, while the expected size is {expected_size} bytes'
            # open a critical dialog
            msg = QtWidgets.QMessageBox.critical(self, "Error", dmsg, QtWidgets.QMessageBox.Ok,
                                                 QtWidgets.QMessageBox.Ok)
            return

        if file_size > expected_size:
            dmsg = f'Warning: The file size is larger than expected.\nThis means that parts of the file will be ignored. The file size is {file_size} bytes, while the expected size is {expected_size} bytes'
            # open a warning dialog
            msg = QtWidgets.QMessageBox.warning(self, "Warning", dmsg, QtWidgets.QMessageBox.Ok,
                                                QtWidgets.QMessageBox.Ok)

        # read centre slice
        offset = 0
        slice_size = -1
        if dimensionality == 3:
            # read the slice indicated by the user
            slice_size = shape[1] * shape[0]
            offset = pars['preview_slice'] * slice_size

        # use the cilRawCroppedReader to read the slice
        reader2 = cilRawCroppedReader()
        reader2.SetFileName(self.fname)
        reader2.SetTargetZExtent((pars['preview_slice'], pars['preview_slice']))
        reader2.SetBigEndian(isBigEndian)
        reader2.SetIsFortran(isFortran)
        reader2.SetTypeCodeName(dt.name)
        reader2.SetStoredArrayShape(shape)
        reader2.Update()
        # image = reader2.GetOutput()

        # rawfname = os.path.join(tempfile.gettempdir(),"test.raw")

        # offset = offset * bytes_per_element
        # slices_to_read = 1
        # if shape[2] > 1:
        #     slices_to_read = 2
        # with open(self.fname, 'br') as f:
        #     f.seek(offset)
        #     raw_data = f.read(slice_size*bytes_per_element* slices_to_read)
        #     with open(rawfname, 'wb') as f2:
        #         f2.write(raw_data)

        # reader2 = vtk.vtkImageReader2()
        # reader2.SetFileName(rawfname)

        # vtktype = Converter.dtype_name_to_vtkType[dt.name]
        # reader2.SetDataScalarType(vtktype)

        # if isBigEndian:
        #     reader2.SetDataByteOrderToBigEndian()
        # else:
        #     reader2.SetDataByteOrderToLittleEndian()

        # reader2.SetFileDimensionality(len(shape))
        # vtkshape = shape[:]
        # if not isFortran:
        #     # need to reverse the shape (again)
        #     vtkshape = shape[::-1]
        # # vtkshape = shape[:]
        # slice_idx = 0
        # if dimensionality == 3:
        #     slice_idx = vtkshape[2]//2
        # reader2.SetDataExtent(0, vtkshape[0]-1, 0, vtkshape[1]-1, slice_idx, slice_idx+slices_to_read-1)
        # # DataSpacing and DataOrigin should be added to the interface
        # reader2.SetDataSpacing(1, 1, 1)
        # reader2.SetDataOrigin(0, 0, 0)

        # print("reading")
        # reader2.Update()
        # read one slice in the middle and display it in a viewer in a modal dialog

        diag = QtWidgets.QDialog(parent=self)
        diag.setModal(True)
        if dimensionality == 3:
            if pars['is_fortran'] is True:
                slicing = 'image'
            else:
                slicing = 'width'
            diag.setWindowTitle(f"Preview: {slicing} = {pars['preview_slice']}")
        else:
            diag.setWindowTitle(f'Preview Image')
        diag.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        diag.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint)
        # add a layout
        verticalLayout = QtWidgets.QVBoxLayout(diag)
        verticalLayout.setContentsMargins(10, 10, 10, 10)

        # add a CILViewer widget
        sc = QCILViewerWidget(diag, viewer=viewer2D, enableSliderWidget=False)
        sc.viewer.setInputData(reader2.GetOutput())

        # add it to the layout of the dialog
        verticalLayout.addWidget(sc)
        # add the layout to the dialog
        diag.setLayout(verticalLayout)

        # save the dialog and canvas so that it doesn't crash
        self.preview_dialog = diag
        self.preview_mpl_canvas = sc

        # the dialog must delete the temp file when it is closed
        # diag.finished.connect(lambda: os.remove(rawfname))
        # finally open the dialog
        diag.open()


class HDF5InputDialog(FormDialog):
    '''
    This is a dialog window which allows the user to set:
    - the dataset name
    - whether the Z axis should be downsampled (should not be done for acquisition data)
    
    For selecting the dataset name, this dialog uses a table widget to display the
    contents of the HDF5 file.

    Parameters
    ----------
    parent : QWidget
        The parent widget.  
    fname : str
        The name of the HDF5 file.
    '''

    def __init__(self, parent, fname):
        super(HDF5InputDialog, self).__init__(parent, fname)
        title = "Config for " + os.path.basename(fname)
        self.file_name = fname
        self.setWindowTitle(title)
        fw = self.formWidget

        # Browser for dataset name: --------------------------------------
        # create input text for starting group
        hl, _, line_edit, push_button = self.createLineEditForDatasetName()

        # set the focus on the Browse button
        push_button.setDefault(True)
        # create table widget
        tw = self.createTableWidget()

        dataset_selector_widget = QtWidgets.QWidget()

        vl = QtWidgets.QVBoxLayout()

        # add Widgets to layout
        vl.addLayout(hl)
        vl.addWidget(push_button)
        vl.addWidget(tw)

        dataset_selector_widget.setLayout(vl)

        fw.addSpanningWidget(QLabel("Select Dataset:"), 'dataset_selector_title')

        fw.addSpanningWidget(dataset_selector_widget, 'dataset_selector_widget')

        self.tableWidget = tw
        self.push_button = push_button
        self.line_edit = line_edit

        # ---------------------------------------------------------------

        fw.addSeparator('dataset_selector_separator')

        # dimensionality:
        datasetLabel = QLabel("Dataset Name")
        valueEntry = QLineEdit()
        valueEntry.setEnabled(False)
        fw.addWidget(valueEntry, datasetLabel, "dataset_name")
        self.line_edit.textChanged.connect(self.datasetLineEditChanged)

        # is it Acquisition Data?
        dtypeLabel = QLabel("Resample on Z Axis: ")
        dtypeValue = QComboBox()
        dtypeValue.addItems(["False", "True"])
        fw.addWidget(dtypeValue, dtypeLabel, 'resample_z')

        self.Ok.clicked.connect(self.onOkClicked)

        self.setDefaultDatasetName()
        self.hdf5_attrs = {}

    def setDefaultDatasetName(self):
        '''
        Set the default dataset name to the first entry, as dictated by the
        NXTomo standard, and also CIL's NEXUSDataReader/Writer standard.
        Or if that does not exist in the file, set the default to the root group.
        '''
        nxtomo_dataset_name = "/entry1/tomo_entry/data/data"
        # check if the dataset exists:
        with h5py.File(self.file_name, 'r') as f:

            if nxtomo_dataset_name in f:
                obj = f[nxtomo_dataset_name]
                if isinstance(obj, h5py._hl.dataset.Dataset):
                    self.current_group = nxtomo_dataset_name
                    self.line_edit.setText(nxtomo_dataset_name)
                    return
        # if the dataset does not exist, set the default to the root group:
        self.current_group = '/'
        self.line_edit.setText(self.current_group)

    def onOkClicked(self):
        ''' Will need to override this to add further methods
        when the OK button is clicked.
        
        This checks if the dataset name is valid.'''
        dataset_name = self.widgets['dataset_name_field'].text()
        with h5py.File(self.file_name, 'r') as f:
            try:
                obj = f[dataset_name]
            except:
                error_dialog = ErrorDialog(self, "Error", "Could not open: " + dataset_name)
                error_dialog.open()
                return

            if not isinstance(obj, h5py._hl.dataset.Dataset):
                error_dialog = ErrorDialog(self, "Error", "Not a dataset: " + dataset_name)
                error_dialog.open()
                return

    def getHDF5Attributes(self):
        '''
        Returns a dictionary of attributes required for reading the HDF5 file.

        These are the attributes set by the user in this dialog:
        - dataset_name
        - resample_z
        '''
        widgets = self.formWidget.widgets

        self.hdf5_attrs['dataset_name'] = widgets['dataset_name_field'].text()
        self.hdf5_attrs['resample_z'] = bool(widgets['resample_z_field'].currentIndex())

        return self.hdf5_attrs

    def createTableWidget(self):
        '''
        Create a table widget to display the contents of the HDF5 file.
        '''
        tableWidget = QtWidgets.QTableWidget()
        tableWidget.itemDoubleClicked.connect(self.fillLineEditWithDoubleClickedTableItem)
        tableWidget.setColumnWidth(1, 40)
        header = tableWidget.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        return tableWidget

    def createLineEditForDatasetName(self):
        '''
        Create a line edit for the user to enter the dataset name.
        '''
        pb = QtWidgets.QPushButton()
        pb.setText("Browse for Dataset...")
        pb.clicked.connect(self.descendHDF5AndFillTable)

        up = QtWidgets.QPushButton()
        up.setIcon(QtWidgets.QApplication.style().standardPixmap((QtWidgets.QStyle.SP_ArrowUp)))
        up.clicked.connect(self.goToParentGroup)
        up.setFixedSize(QtCore.QSize(30, 30))

        le = QtWidgets.QLineEdit(self)
        le.returnPressed.connect(self.descendHDF5AndFillTable)
        le.setClearButtonEnabled(True)

        hl = QtWidgets.QHBoxLayout()
        hl.addWidget(up)
        hl.addWidget(le)

        return hl, up, le, pb

    def datasetLineEditChanged(self, text):
        '''
        This method is called when the text in the line edit is changed.
        '''
        self.widgets['dataset_name_field'].setText(text)

    def fillLineEditWithDoubleClickedTableItem(self, item):
        '''
        This method is called when a table item is double clicked.
        It will fill the line edit with the path to the selected item.
        It will then descend into the selected item and fill the table with
        the contents of the selected item.
        '''
        row = item.row()
        fsitem = self.tableWidget.item(row, 0)
        new_group = fsitem.text()
        current_group = self.line_edit.text()
        with h5py.File(self.file_name, 'r') as f:
            # Try to use the current group entered in the line edit
            # if it does not exist, use the current group saved to memory,
            # which was the last group that was successfully opened.
            try:
                f[current_group]
            except KeyError:
                current_group = self.current_group

            new_path = current_group + "/" + fsitem.text()

            if new_group in f[current_group]:
                self.line_edit.setText(new_path)
                self.current_group = new_path
                self.descendHDF5AndFillTable()
            else:
                error_dialog = ErrorDialog(
                    self, "Error", "The selected item could not be opened.",
                    f"{new_path} either does not exist, or is not a group or dataset, so can't be opened.")
                error_dialog.open()

    def descendHDF5AndFillTable(self):
        '''
        This descends into the HDF5 file and fills the table with the contents
        of the group.
        '''
        # set OverrideCursor to WaitCursor
        QtGui.QGuiApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        group = self.line_edit.text()

        with h5py.File(self.file_name, 'r') as f:
            try:
                obj = f[group]
            except:
                error_dialog = ErrorDialog(self, "Error", "Could not open group: " + group)
                error_dialog.open()
                QtGui.QGuiApplication.restoreOverrideCursor()
                return

            list_of_items = []

            if type(obj) in [h5py._hl.group.Group, h5py._hl.files.File]:
                for key in obj.keys():
                    list_of_items.append((key, str(obj[key])))
            elif isinstance(obj, h5py._hl.dataset.Dataset):
                for key in obj.attrs.keys():
                    list_of_items.append((key, obj.attrs[key]))

        self.loadIntoTableWidget(list_of_items)
        # restore OverrideCursor
        QtGui.QGuiApplication.restoreOverrideCursor()

    def loadIntoTableWidget(self, data):
        '''
        This loads the data into the table widget.
        '''
        if len(data) <= 0:
            return
        self.tableWidget.setRowCount(len(data))
        self.tableWidget.setColumnCount(len(data[0]))
        for i, v in enumerate(data):
            for j, w in enumerate(v):
                item = QtWidgets.QTableWidgetItem(str(w))
                item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                if j == 1:
                    item.setToolTip(str(w))
                self.tableWidget.setItem(i, j, item)

        self.tableWidget.setHorizontalHeaderLabels(['Name', 'Contents'])

        self.tableWidget.sortItems(1, order=QtCore.Qt.AscendingOrder)
        self.tableWidget.resizeColumnsToContents()

    def goToParentGroup(self):
        '''
        This method is called when the up button is clicked.
        It will go to the parent group of the current group.
        '''
        le = self.line_edit
        parent_group = self.getCurrentParentGroup()
        le.setText(str(parent_group))
        self.current_group = parent_group
        self.descendHDF5AndFillTable()

    def getCurrentGroup(self):
        '''
        This method returns the current group.
        '''
        return self.current_group

    def getCurrentParentGroup(self):
        '''
        This method returns the parent group of the current group.
        If there is no parent group, it returns the current group,
        which is the root group.
        '''
        current_group = self.getCurrentGroup()
        if current_group != "/" and current_group != "//" and current_group != "":
            item_to_remove = "/" + current_group.split("/")[-1]
            parent_group = current_group[:-len(item_to_remove)]
        else:
            parent_group = current_group

        if parent_group == "":
            parent_group = "/"

        return parent_group
