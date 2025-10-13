import unittest
import os
import sys

from unittest import mock
from unittest.mock import patch

from ccpi.viewer.QCILViewer3DToolBar import QCILViewer3DToolBar
from ccpi.viewer.CILViewer import CILViewer

from qtpy.QtWidgets import QMainWindow
from qtpy.QtWidgets import QApplication, QLabel, QFrame, QDoubleSpinBox, QCheckBox, QPushButton, QLineEdit, QComboBox, QWidget
from qtpy.QtCore import QSettings

from eqt.ui import FormDialog
from functools import partial

# skip the tests on GitHub actions
if os.environ.get('CONDA_BUILD', '0') == '1':
    skip_as_conda_build = True
else:
    skip_as_conda_build = False

print("skip_as_conda_build is set to ", skip_as_conda_build)

from .qt_utils import TestCaseQt


@unittest.skipIf(skip_as_conda_build, "On conda builds do not do any test with interfaces")
class TestQCILViewer3DToolBar(TestCaseQt):

    def setUp(self):
        self.app = TestCaseQt.get_QApplication([])
        self.parent = QMainWindow()
        self.viewer = CILViewer()
        self.settings = QSettings()

    def test_init(self):
        toolbar = QCILViewer3DToolBar(self.parent, self.viewer)
        assert toolbar is not None
