#
#   Author 2022 Samuel Jones
#   Copyright 2022 SCD Rutherford Appleton Laboratory UKRI
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

from dataclasses import dataclass
from vtkmodules.vtkRenderingCore import vtkCamera


@dataclass(init=False)
class CameraData:
    position: list
    focalPoint: list
    viewUp: list

    def __init__(self, camera: vtkCamera):
        self.position = camera.GetPosition()
        self.focalPoint = camera.GetFocalPoint()
        self.viewUp = camera.GetViewUp()

    def copy_data_to_other_camera(self, other_cam: vtkCamera):
        other_cam.SetPosition(*self.position)
        other_cam.SetFocalPoint(*self.focalPoint)
        other_cam.SetViewUp(*self.viewUp)
