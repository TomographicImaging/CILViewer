#
#   Copyright 2022 STFC, United Kingdom Research and Innovation
#
#   Author 2022 Samuel Jones
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

import vtk

from ccpi.viewer.utils import CameraData


class CameraDataTest(unittest.TestCase):

    def setUp(self):
        self.camera = vtk.vtkCamera()
        self.cam_pos = (1., 1., 1.)
        self.focal_pos = (2., 2., 2.)
        self.view_up = (0.57735026, 0.57735026, 0.57735026)
        self.camera.SetPosition(*self.cam_pos)
        self.camera.SetFocalPoint(*self.focal_pos)
        self.camera.SetViewUp(*self.view_up)

        self.data = CameraData(self.camera)

    def test_init_sets_all_values(self):
        self.assertEqual(self.data.position, self.cam_pos)
        self.assertEqual(self.data.focalPoint, self.focal_pos)
        self.assertAlmostEqual(self.data.viewUp[0], self.view_up[0])
        self.assertAlmostEqual(self.data.viewUp[1], self.view_up[1])
        self.assertAlmostEqual(self.data.viewUp[2], self.view_up[2])

    def test_copy_data_to_camera_does_so(self):
        camera_to_copy_to = vtk.vtkCamera()

        self.assertNotEqual(self.cam_pos, camera_to_copy_to.GetPosition())
        self.assertNotEqual(self.focal_pos, camera_to_copy_to.GetFocalPoint())
        self.assertNotEqual(self.view_up, camera_to_copy_to.GetViewUp())

        CameraData.CopyDataToCamera(self.data, camera_to_copy_to)

        self.assertEqual(self.cam_pos, camera_to_copy_to.GetPosition())
        self.assertEqual(self.focal_pos, camera_to_copy_to.GetFocalPoint())
        self.assertAlmostEqual(self.view_up[0], camera_to_copy_to.GetViewUp()[0])
        self.assertAlmostEqual(self.view_up[1], camera_to_copy_to.GetViewUp()[1])
        self.assertAlmostEqual(self.view_up[2], camera_to_copy_to.GetViewUp()[2])
