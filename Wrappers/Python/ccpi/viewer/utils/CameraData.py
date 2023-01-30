#
#   Copyright 2022 STFC, United Kingdom Research and Innovation
#
#   Author 2022 Samuel Jones, Laura Murgatroyd
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

import vtk


@dataclass(init=False)
class CameraData:
    '''
    A dataclass to store the camera position, focal point and view up
    '''
    position: list
    focalPoint: list
    viewUp: list

    def __init__(self, camera: vtk.vtkCamera):
        self.position = camera.GetPosition()
        self.focalPoint = camera.GetFocalPoint()
        self.viewUp = camera.GetViewUp()

    @staticmethod
    def CopyDataToCamera(camera_data, vtkcamera):
        '''
        Copy the camera_data to a vtkcamera
        
        Parameters
        ----------
        camera_data : CameraData
            The camera data to copy
        vtkcamera : vtkCamera
            The vtk camera to copy to.
        '''
        vtkcamera.SetPosition(*camera_data.position)
        vtkcamera.SetFocalPoint(*camera_data.focalPoint)
        vtkcamera.SetViewUp(*camera_data.viewUp)
