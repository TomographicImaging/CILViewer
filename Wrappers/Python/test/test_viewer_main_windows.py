import unittest
from unittest import mock

from PySide2.QtWidgets import QMainWindow
import os

from unittest import mock
from PySide2.QtCore import QSettings, QThreadPool
from PySide2.QtWidgets import QApplication, QLabel, QFrame, QDoubleSpinBox, QCheckBox, QPushButton, QLineEdit, QComboBox, QWidget

import sys

from ccpi.viewer.ui.main_windows import ViewerMainWindow

# skip the tests on GitHub actions
if os.environ.get('CONDA_BUILD', '0') == '1':
    skip_as_conda_build = True
else:
    skip_as_conda_build = False

print("skip_as_conda_build is set to ", skip_as_conda_build)

if not skip_as_conda_build:
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
else:
    skip_test = True


@unittest.skipIf(skip_as_conda_build, "On conda builds do not do any test with interfaces")
class TestViewerMainWindow(unittest.TestCase):

    def test_init(self):
        vmw = ViewerMainWindow(title="Testing Title", app_name="testing app name")
        assert vmw is not None


if __name__ == '__main__':
    unittest.main()
