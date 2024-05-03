#   Copyright 2023 STFC, United Kingdom Research and Innovation
#
#   Author 2023 Laura Murgatroyd
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import unittest
from unittest import mock
import os

from ccpi.viewer.CILViewer import CILViewerBase

# skip the tests on GitHub actions
if os.environ.get('CONDA_BUILD', '0') == '1':
    skip_test = True
else:
    skip_test = False

print("skip_test is set to ", skip_test)

@unittest.skipIf(skip_test, "Skipping tests on GitHub Actions")
class CILViewerBaseTest(unittest.TestCase):
    def setUp(self):
        '''Creates an instance of the CIL viewer base class.'''
        self.CILViewerBase_instance = CILViewerBase()

    def test_setAxisLabels(self):  
        '''Edits the labels in the axes widget and checks they have been set correctly.
        The test is performed with overwrite flag set to default, True, or False.'''
        labels = ['a','b','c']
        self.CILViewerBase_instance.setAxisLabels(labels)
        new_labels = self.CILViewerBase_instance.getCurrentAxisLabelsText()   
        self.assertEqual(new_labels, labels)
        self.assertEqual(self.CILViewerBase_instance.axisLabelsText, labels)

        labels_2 = ['c','d','e']
        self.CILViewerBase_instance.setAxisLabels(labels_2,False)
        new_labels = self.CILViewerBase_instance.getCurrentAxisLabelsText()   
        self.assertEqual(new_labels, labels_2)
        self.assertEqual(self.CILViewerBase_instance.axisLabelsText, labels)


@unittest.skipIf(skip_test, "Skipping tests on GitHub Actions")
class CILViewer3DTest(unittest.TestCase):

    def setUp(self):
        self.cil_viewer = CILViewerBase()

    def test_getSliceColorPercentiles_returns_correct_percentiles_when_slice_values_start_at_zero(self):
        self.cil_viewer.getSliceMapRange = mock.MagicMock(return_value=[40, 50])
        self.cil_viewer.getSliceMapWholeRange = mock.MagicMock(return_value=[0, 50])
        expected_percentages = (80.0, 100.0)
        actual_percentages = self.cil_viewer.getSliceColorPercentiles()
        self.assertEqual(expected_percentages, actual_percentages)

    def test_getSliceColorPercentiles_returns_correct_percentiles_when_slice_values_start_at_non_zero(self):
        self.cil_viewer.getSliceMapRange = mock.MagicMock(return_value=[40, 50])
        self.cil_viewer.getSliceMapWholeRange = mock.MagicMock(return_value=[10, 50])
        expected_percentages = (75.0, 100.0)
        actual_percentages = self.cil_viewer.getSliceColorPercentiles()
        self.assertEqual(expected_percentages, actual_percentages)

    def test_multiple_widgets_cant_be_saved_with_same_name(self):
        widget1 = mock.MagicMock()
        widget2 = mock.MagicMock()
        widget_name = "widget1"
        self.cil_viewer.addWidgetReference(widget1, widget_name)
        with self.assertRaises(ValueError):
            self.cil_viewer.addWidgetReference(widget2, widget_name)



if __name__ == '__main__':
    unittest.main()
