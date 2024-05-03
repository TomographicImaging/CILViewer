#
import unittest
import os
from ccpi.viewer.standalone_viewer import standalone_viewer
from PySide2 import QtWidgets

# skip the tests on GitHub actions
if os.environ.get('CONDA_BUILD', '0') == '1':
    skip_test = True
else:
    skip_test = False

print("skip_test is set to ", skip_test)

@unittest.skipIf(skip_test, "Skipping tests on GitHub Actions")
class StandaloneViewerTest(unittest.TestCase):
    def setUp(self):
        self.standalone_viewer_instance = standalone_viewer("Standalone Viewer Test", viewer1_type='2D', viewer2_type='3D')
        print(self.standalone_viewer_instance.window)
        print(self.standalone_viewer_instance.window.viewers)

    def test_close_app(self):
        self.standalone_viewer_instance.__del__()
        