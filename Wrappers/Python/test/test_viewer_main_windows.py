import os
import sys
import unittest
from unittest import mock

import vtk
from ccpi.viewer.CILViewer import CILViewer
from ccpi.viewer.CILViewer2D import CILViewer2D
from ccpi.viewer.ui.main_windows import ViewerMainWindow
from PySide2.QtWidgets import QApplication

# skip the tests on GitHub actions
if os.environ.get('CONDA_BUILD', '0') == '1':
    skip_as_conda_build = True
else:
    skip_as_conda_build = False

print("skip_as_conda_build is set to ", skip_as_conda_build)

_instance = None


@unittest.skipIf(skip_as_conda_build, "On conda builds do not do any test with interfaces")
class TestViewerMainWindow(unittest.TestCase):
    ''' Methods which have their full functionality tested:
    - onAppSettingsDialogAccepted
    - setDefaultDownsampledSize
    - getDefaulDownsampledSize
    - getTargetImageSize
    - updateViewerCoords
    '''

    def setUp(self):
        global _instance
        if _instance is None:
            _instance = QApplication(sys.argv)

    def test_init(self):
        vmw = ViewerMainWindow(title="Testing Title", app_name="testing app name")
        assert vmw is not None

    def test_init_calls_super_init(self):
        vmw = ViewerMainWindow(title="Testing Title", app_name="testing app name")
        # If the super init is called, then the following attributes should be set:
        assert vmw.app_name == "testing app name"
        assert vmw.threadpool is not None
        assert vmw.progress_windows == {}

    def test_createAppSettingsDialog_calls_setAppSettingsDialogWidgets(self):
        vmw = ViewerMainWindow(title="Testing Title", app_name="testing app name")
        vmw.setAppSettingsDialogWidgets = mock.MagicMock()
        vmw.setViewerSettingsDialogWidgets = mock.MagicMock()
        vmw.createAppSettingsDialog()
        vmw.setAppSettingsDialogWidgets.assert_called_once()
        vmw.setViewerSettingsDialogWidgets.assert_called_once()

    def test_acceptViewerSettings_when_gpu_checked(self):

        vmw = self._setup_acceptViewerSettings_tests()

        vmw.acceptViewerSettings()

        vmw.settings.assert_has_calls(
            [mock.call.setValue('use_gpu_volume_mapper', True),
             mock.call.setValue('vis_size', 1.0)], any_order=True)

        assert isinstance(vmw.viewers[0].volume_mapper, vtk.vtkSmartVolumeMapper)

    def test_acceptViewerSettings_when_gpu_unchecked(self):

        vmw, settings_dialog = self._setup_acceptViewerSettings_tests()

        vmw.acceptViewerSettings(settings_dialog)

        vmw.settings.assert_has_calls(
            [mock.call.setValue('use_gpu_volume_mapper', False),
             mock.call.setValue('vis_size', 1.0)], any_order=True)

        assert isinstance(vmw.viewers[0].volume_mapper, vtk.vtkFixedPointVolumeRayCastMapper)

    def _setup_acceptViewerSettings_tests(self):
        vmw = ViewerMainWindow(title="Testing Title", app_name="testing app name")
        vmw.settings = mock.MagicMock()
        vmw.settings.setValue = mock.MagicMock()
        vis_size_field = mock.MagicMock()
        vis_size_field.value.return_value = 1.0
        gpu_checkbox_field = mock.MagicMock()
        gpu_checkbox_field.isChecked.return_value = True
        dark_checkbox_field = mock.MagicMock()
        dark_checkbox_field.isChecked.return_value = False
        settings_dialog = mock.MagicMock()
        settings_dialog.widgets = {
            'vis_size_field': vis_size_field,
            'gpu_checkbox_field': gpu_checkbox_field,
            'dark_checkbox_field': dark_checkbox_field
        }
        viewer3D = CILViewer()
        viewer3D.volume_mapper = None
        vmw._viewers = [viewer3D]
        vmw._vs_dialog = settings_dialog
        return vmw

    def test_acceptViewerSettings_when_gpu_unchecked(self):
        vmw = self._setup_acceptViewerSettings_tests()
        vmw._vs_dialog.widgets['gpu_checkbox_field'].isChecked.return_value = False

        vmw.acceptViewerSettings()
        vmw.settings.assert_has_calls(
            [mock.call.setValue('use_gpu_volume_mapper', False),
             mock.call.setValue('vis_size', 1.0)], any_order=True)

        assert isinstance(vmw.viewers[0].volume_mapper, vtk.vtkFixedPointVolumeRayCastMapper)

    def test_setDefaultDownsampledSize(self):
        vmw = ViewerMainWindow(title="Testing Title", app_name="testing app name")
        vmw.setDefaultDownsampledSize(5)
        assert vmw.default_downsampled_size == 5

    def test_getDefaultDownsampledSize(self):
        vmw = ViewerMainWindow(title="Testing Title", app_name="testing app name")
        # Test what the default value is:
        assert vmw.getDefaultDownsampledSize() == 512**3
        vmw.default_downsampled_size = 5
        assert vmw.getDefaultDownsampledSize() == 5

    def test_getTargetImageSize_when_vis_size_is_None(self):
        vmw = ViewerMainWindow(title="Testing Title", app_name="testing app name")
        vmw.settings.setValue("vis_size", None)
        vmw.getDefaultDownsampledSize = mock.MagicMock()
        vmw.getDefaultDownsampledSize.return_value = 512**3
        returned_target_size = vmw.getTargetImageSize()
        vmw.getDefaultDownsampledSize.assert_called_once()
        assert (returned_target_size == 512**3)

    def test_getTargetImageSize_when_vis_size_is_not_None(self):
        vmw = ViewerMainWindow(title="Testing Title", app_name="testing app name")
        vmw.settings.setValue("vis_size", 5)
        vmw.getDefaultDownsampledSize = mock.MagicMock()
        returned_target_size = vmw.getTargetImageSize()
        vmw.getDefaultDownsampledSize.assert_not_called()
        assert (returned_target_size == 5 * (1024**3))

    def test_updateViewerCoords_with_display_unsampled_coords_selected(self):
        vmw = ViewerMainWindow(title="Testing Title", app_name="testing app name")
        viewer2D = CILViewer2D()
        viewer2D.visualisation_downsampling = [2, 2, 2]
        viewer2D.img3D = vtk.vtkImageData()
        viewer2D.setDisplayUnsampledCoordinates = mock.MagicMock()
        viewer2D.updatePipeline = mock.MagicMock()
        vmw.viewer_coords_dock.viewers = [viewer2D]
        viewer_coords_widgets = vmw.viewer_coords_dock.getWidgets()
        viewer_coords_widgets['coords_combo_field'].setCurrentIndex(0)
        viewer_coords_widgets['coords_warning_field'].setVisible = mock.MagicMock()
        vmw.updateViewerCoords()

        # Expect display unsampled coords to be called with True
        # and the warning field to be visible:
        viewer2D.setDisplayUnsampledCoordinates.assert_called_once_with(True)
        viewer_coords_widgets['coords_warning_field'].setVisible.assert_called_once_with(True)
        viewer2D.updatePipeline.assert_called_once()

        viewer2D.updatePipeline = mock.MagicMock()  # reset call count
        viewer2D.visualisation_downsampling = [1, 1, 1]
        vmw.updateViewerCoords()
        # Expect the warning field to be hidden:
        viewer_coords_widgets['coords_warning_field'].setVisible.assert_called_with(False)
        viewer2D.updatePipeline.assert_called_once()

    def test_updateViewerCoords_with_display_downsampled_coords_selected(self):
        vmw = ViewerMainWindow(title="Testing Title", app_name="testing app name")
        viewer2D = CILViewer2D()
        viewer2D.visualisation_downsampling = [2, 2, 2]
        viewer2D.img3D = vtk.vtkImageData()
        viewer2D.setDisplayUnsampledCoordinates = mock.MagicMock()
        viewer2D.updatePipeline = mock.MagicMock()
        vmw.viewer_coords_dock.viewers = [viewer2D]
        viewer_coords_widgets = vmw.viewer_coords_dock.getWidgets()
        viewer_coords_widgets['coords_combo_field'].setCurrentIndex(1)
        viewer_coords_widgets['coords_warning_field'].setVisible = mock.MagicMock()
        vmw.updateViewerCoords()

        # Expect display unsampled coords to be called with False
        # and the warning field to be hidden:
        viewer2D.setDisplayUnsampledCoordinates.assert_called_with(False)
        viewer_coords_widgets['coords_warning_field'].setVisible.assert_called_once_with(False)
        viewer2D.updatePipeline.assert_called()

    def test_updateViewerCoords_with_3D_viewer(self):
        vmw = ViewerMainWindow(title="Testing Title", app_name="testing app name")
        viewer3D = CILViewer()
        viewer3D.visualisation_downsampling = [2, 2, 2]
        viewer3D.updatePipeline = mock.MagicMock()
        viewer3D.setDisplayUnsampledCoordinates = mock.MagicMock()
        vmw.viewer_coords_dock.viewers = [viewer3D]
        viewer_coords_widgets = vmw.viewer_coords_dock.getWidgets()
        viewer_coords_widgets['coords_combo_field'].setCurrentIndex(1)
        viewer_coords_widgets['coords_warning_field'].setVisible = mock.MagicMock()
        vmw.updateViewerCoords()

        # Expect we don't call anything:
        viewer3D.setDisplayUnsampledCoordinates.assert_not_called()
        viewer_coords_widgets['coords_warning_field'].setVisible.assert_not_called()
        viewer3D.updatePipeline.assert_not_called()

    def test_updateViewerCoords_with_no_img3D(self):
        vmw = ViewerMainWindow(title="Testing Title", app_name="testing app name")
        viewer2D = CILViewer2D()
        viewer2D.visualisation_downsampling = [2, 2, 2]
        viewer2D.img3D = None
        viewer2D.setDisplayUnsampledCoordinates = mock.MagicMock()
        viewer2D.updatePipeline = mock.MagicMock()
        vmw.viewer_coords_dock.viewers = [viewer2D]
        viewer_coords_widgets = vmw.viewer_coords_dock.getWidgets()
        viewer_coords_widgets['coords_combo_field'].setCurrentIndex(1)
        viewer_coords_widgets['coords_warning_field'].setVisible = mock.MagicMock()
        vmw.updateViewerCoords()

        # Expect we don't call anything:
        viewer2D.setDisplayUnsampledCoordinates.assert_not_called()
        viewer_coords_widgets['coords_warning_field'].setVisible.assert_not_called()
        viewer2D.updatePipeline.assert_not_called()


if __name__ == '__main__':
    unittest.main()
