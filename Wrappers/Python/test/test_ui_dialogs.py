import unittest
from unittest import mock
from ccpi.viewer.ui.dialogs import ViewerSettingsDialog, HDF5InputDialog, RawInputDialog, SaveableRawInputDialog
from eqt.ui.SessionDialogs import AppSettingsDialog

from PySide2.QtWidgets import QMainWindow
import os

from unittest import mock
from unittest.mock import patch
from PySide2.QtWidgets import QApplication, QLabel, QFrame, QDoubleSpinBox, QCheckBox, QPushButton, QLineEdit, QComboBox, QWidget
from PySide2.QtCore import QSettings
from eqt.ui import FormDialog
from functools import partial

import sys

# skip the tests on GitHub actions
if os.environ.get('CONDA_BUILD', '0') == '1':
    skip_as_conda_build = True
else:
    skip_as_conda_build = False

print("skip_as_conda_build is set to ", skip_as_conda_build)

_instance = None


@unittest.skipIf(skip_as_conda_build, "On conda builds do not do any test with interfaces")
class TestViewerSettingsDialog(unittest.TestCase):

    def setUp(self):
        global _instance
        if _instance is None:
            _instance = QApplication(sys.argv)

    def test_init(self):
        parent = QMainWindow()
        vsd = ViewerSettingsDialog(parent)
        assert vsd is not None

    @mock.patch.object(AppSettingsDialog, '__init__')
    @mock.patch.object(ViewerSettingsDialog, '_addViewerSettingsWidgets')
    def test_init_calls_init_app_settings_and_addViewerSettingsWidgets(self, mock_addViewerSettingsWidgets,
                                                                       mock_app_settings_init):
        parent = QMainWindow()
        ViewerSettingsDialog(parent)
        mock_app_settings_init.assert_called_once_with(parent)
        mock_addViewerSettingsWidgets.assert_called_once()

    def test_addViewerSettingsWidgets(self):
        parent = QMainWindow()
        vsd = ViewerSettingsDialog(parent)

        #Check we have the widgets that we expect:
        assert isinstance(vsd.getWidget('viewer_settings_separator'), QFrame)
        assert isinstance(vsd.getWidget('viewer_settings_title'), QLabel)
        assert isinstance(vsd.getWidget('vis_size'), QDoubleSpinBox)
        assert isinstance(vsd.getWidget('vis_size', 'label'), QLabel)
        assert isinstance(vsd.getWidget('adv_separator'), QFrame)
        assert isinstance(vsd.getWidget('adv_settings_title'), QLabel)
        assert isinstance(vsd.getWidget('gpu_checkbox'), QCheckBox)


@unittest.skipIf(skip_as_conda_build, "On conda builds do not do any test with interfaces")
class TestHDF5InputDialog(unittest.TestCase):
    # TODO: test creation of HDF5 dataset browsing widget functionality

    def setUp(self):
        global _instance
        if _instance is None:
            _instance = QApplication(sys.argv)
        self.parent = QMainWindow()
        self.fname = "test.h5"

    def test_init(self):
        HDF5InputDialog.createLineEditForDatasetName = mock.Mock()
        HDF5InputDialog.createLineEditForDatasetName.return_value = (None, None, QLineEdit(), QPushButton())
        HDF5InputDialog.setDefaultDatasetName = mock.Mock()
        h5id = HDF5InputDialog(self.parent, self.fname)
        assert h5id is not None

    def test_init_creates_widgets(self):
        HDF5InputDialog.createLineEditForDatasetName = mock.Mock()
        HDF5InputDialog.createLineEditForDatasetName.return_value = (None, None, QLineEdit(), QPushButton())
        HDF5InputDialog.setDefaultDatasetName = mock.Mock()
        h5id = HDF5InputDialog(self.parent, self.fname)

        #Check we have the widgets that we expect:
        assert isinstance(h5id.getWidget('dataset_selector_title'), QLabel)
        assert isinstance(h5id.getWidget('dataset_selector_widget'), QWidget)
        assert isinstance(h5id.getWidget('dataset_selector_separator'), QFrame)
        assert isinstance(h5id.getWidget('dataset_name', 'label'), QLabel)
        assert isinstance(h5id.getWidget('dataset_name', 'field'), QLineEdit)
        assert isinstance(h5id.getWidget('resample_z'), QComboBox)
        assert isinstance(h5id.getWidget('resample_z', 'label'), QLabel)

    def test_getHDF5Attributes(self):
        HDF5InputDialog.createLineEditForDatasetName = mock.Mock()
        HDF5InputDialog.createLineEditForDatasetName.return_value = (None, None, QLineEdit(), QPushButton())
        HDF5InputDialog.setDefaultDatasetName = mock.Mock()
        h5id = HDF5InputDialog(self.parent, self.fname)
        assert h5id.getHDF5Attributes() == {'dataset_name': '', 'resample_z': False}
        h5id.getWidget('dataset_name', 'field').setText('test')
        h5id.getWidget('resample_z').setCurrentText("True")
        assert h5id.getHDF5Attributes() == {'dataset_name': 'test', 'resample_z': True}

    def test_getCurrentGroup(self):
        HDF5InputDialog.createLineEditForDatasetName = mock.Mock()
        HDF5InputDialog.createLineEditForDatasetName.return_value = (None, None, QLineEdit(), QPushButton())
        HDF5InputDialog.setDefaultDatasetName = mock.Mock()
        h5id = HDF5InputDialog(self.parent, self.fname)
        h5id.current_group = '/'
        assert h5id.getCurrentGroup() == '/'

    def test_getCurrentParentGroup_when_parent_exists(self):
        HDF5InputDialog.createLineEditForDatasetName = mock.Mock()
        HDF5InputDialog.createLineEditForDatasetName.return_value = (None, None, QLineEdit(), QPushButton())
        HDF5InputDialog.setDefaultDatasetName = mock.Mock()
        h5id = HDF5InputDialog(self.parent, self.fname)
        h5id.current_group = '/test/child'
        self.assertEqual(h5id.getCurrentParentGroup(), '/test')

    def test_getCurrentParentGroup_when_parent_does_not_exist(self):
        HDF5InputDialog.createLineEditForDatasetName = mock.Mock()
        HDF5InputDialog.createLineEditForDatasetName.return_value = (None, None, QLineEdit(), QPushButton())
        HDF5InputDialog.setDefaultDatasetName = mock.Mock()
        h5id = HDF5InputDialog(self.parent, self.fname)
        h5id.current_group = '/'
        self.assertEqual(h5id.getCurrentParentGroup(), '/')
        h5id.current_group = '//'
        self.assertEqual(h5id.getCurrentParentGroup(), '//')
        h5id.current_group = ''
        self.assertEqual(h5id.getCurrentParentGroup(), '/')

    def test_goToParentGroup(self):
        HDF5InputDialog.createLineEditForDatasetName = mock.Mock()
        HDF5InputDialog.createLineEditForDatasetName.return_value = (None, None, QLineEdit(), QPushButton())
        HDF5InputDialog.setDefaultDatasetName = mock.Mock()
        HDF5InputDialog.getCurrentParentGroup = mock.Mock()
        HDF5InputDialog.getCurrentParentGroup.return_value = 'test'
        HDF5InputDialog.descendHDF5AndFillTable = mock.Mock()
        h5id = HDF5InputDialog(self.parent, self.fname)

        h5id.goToParentGroup()
        HDF5InputDialog.getCurrentParentGroup.assert_called_once()
        HDF5InputDialog.descendHDF5AndFillTable.assert_called_once()
        # check we have moved to parent group:
        assert h5id.current_group == 'test'


@unittest.skipIf(skip_as_conda_build, "On conda builds do not do any test with interfaces")
class TestRawInputDialog(unittest.TestCase):

    def setUp(self):
        global _instance
        if _instance is None:
            _instance = QApplication(sys.argv)
        self.parent = QMainWindow()
        self.fname = "test.raw"

    def test_init(self):
        rdi = RawInputDialog(self.parent, self.fname)
        assert rdi is not None

    def test_init_creates_widgets(self):
        rdi = RawInputDialog(self.parent, self.fname)
        #Check we have the widgets that we expect:
        assert isinstance(rdi.getWidget('dimensionality', 'label'), QLabel)
        assert isinstance(rdi.getWidget('dimensionality', 'field'), QComboBox)
        assert isinstance(rdi.getWidget('dim_Width', 'label'), QLabel)
        assert isinstance(rdi.getWidget('dim_Width', 'field'), QLineEdit)
        assert isinstance(rdi.getWidget('dim_Height', 'label'), QLabel)
        assert isinstance(rdi.getWidget('dim_Height', 'field'), QLineEdit)
        assert isinstance(rdi.getWidget('dim_Images', 'label'), QLabel)
        assert isinstance(rdi.getWidget('dim_Images', 'field'), QLineEdit)
        assert isinstance(rdi.getWidget('dtype', 'label'), QLabel)
        assert isinstance(rdi.getWidget('dtype', 'field'), QComboBox)
        assert isinstance(rdi.getWidget('endianness', 'label'), QLabel)
        assert isinstance(rdi.getWidget('endianness', 'field'), QComboBox)
        assert isinstance(rdi.getWidget('preview_slice', 'label'), QLabel)
        assert isinstance(rdi.getWidget('preview_slice', 'field'), QLineEdit)

    def test_getRawAttrs(self):
        rdi = RawInputDialog(self.parent, self.fname)
        got_raw_attrs = rdi.getRawAttrs()
        expected_raw_attrs = {
            'shape': [0, 0, 0],
            'typecode': 'uint8',
            'is_big_endian': True,
            'is_fortran': True,
            'preview_slice': 0
        }
        assert got_raw_attrs == expected_raw_attrs
        rdi.getWidget('dim_Width', 'field').setText('1')
        rdi.getWidget('dim_Height', 'field').setText('2')
        rdi.getWidget('dim_Images', 'field').setText('3')
        rdi.getWidget('dtype', 'field').setCurrentText('uint16')
        rdi.getWidget('endianness', 'field').setCurrentText('Big Endian')
        rdi.getWidget('preview_slice', 'field').setText("0")
        rdi.getWidget('is_fortran', 'field').setCurrentText("Images-Height-Width")
        assert rdi.getRawAttrs() == {
            'shape': [1, 2, 3],
            'typecode': 'uint16',
            'is_big_endian': True,
            'is_fortran': False,
            'preview_slice': 0
        }

@unittest.skipIf(skip_as_conda_build, "On conda builds do not do any test with interfaces")
class TestSaveableRawInputDialog(unittest.TestCase):

    def setUp(self):
        global _instance
        if _instance is None:
            _instance = QApplication(sys.argv)
        self.parent = QMainWindow()
        self.settings = QSettings()
        self.fname = "test.raw"


    @patch("ccpi.viewer.ui.dialogs.RawInputDialog.__init__")
    def test_init_calls_raw_input_dialog_init(self, mock_init_call):
        mock_init_call.return_value = partial(FormDialog.__init__)
        # expect attribute error after init call:
        with self.assertRaises(AttributeError):
            rdi = SaveableRawInputDialog(self.parent, self.fname, self.settings)
            mock_init_call.assert_called_once()

    def test_init(self):
        rdi = SaveableRawInputDialog(self.parent, self.fname, self.settings)
        assert rdi is not None

    @patch("ccpi.viewer.ui.dialogs.SaveableRawInputDialog._get_settings_save_name")
    def test_save_settings_when_nothing_in_qsettings(self, mock_get_name):
        mock_get_name.return_value = "my_name"
        empty_settings = QSettings('A', 'A')
        rdi = SaveableRawInputDialog(self.parent, self.fname, empty_settings)
        rdi._save_settings()
        the_dict = empty_settings.value('raw_dialog')
        self.assertEqual(empty_settings.allKeys(), ['raw_dialog'])
        self.assertEqual( the_dict, {'my_name': rdi.getAllWidgetStates()})


    @patch("ccpi.viewer.ui.dialogs.SaveableRawInputDialog._get_settings_save_name")
    def test_save_settings_when_soemthing_in_qsettings(self, mock_get_name):
        mock_get_name.return_value = "my_name_2"
        pop_settings = QSettings('C', 'D')
        pop_settings.setValue('raw_dialog', {'hi': "I'm not empty"})
        rdi = SaveableRawInputDialog(self.parent, self.fname, pop_settings)
        rdi._save_settings()
        the_dict = pop_settings.value('raw_dialog')
        self.assertEqual( the_dict, {'hi': "I'm not empty", 'my_name_2': rdi.getAllWidgetStates()})

    @patch("ccpi.viewer.ui.dialogs.SaveableRawInputDialog._get_name_of_state_to_load")
    def test_load_settings(self, mock_get_name):
        mock_get_name.return_value = "state"
        example_qsettings = QSettings('B', 'B')
        rdi = SaveableRawInputDialog(self.parent, self.fname, example_qsettings)
        rdi.getWidget('dim_Images').setText('10')
        example_settings = rdi.getAllWidgetStates()

        example_qsettings = QSettings('B', 'B')
        
        example_qsettings.setValue('raw_dialog', {'state': example_settings})

        rdi2 = SaveableRawInputDialog(self.parent, self.fname, example_qsettings)
        rdi2._load_settings()
        self.assertEqual(rdi2.getWidget('dim_Images').text(), "10")
    

if __name__ == '__main__':
    unittest.main()
