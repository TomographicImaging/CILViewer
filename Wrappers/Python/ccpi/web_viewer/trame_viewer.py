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
import os

from trame.html import vtk, vuetify
from trame.layouts import SinglePageWithDrawer
from vtkmodules.vtkIOImage import vtkMetaImageReader

from ccpi.viewer.utils.conversion import cilHDF5ResampleReader


class TrameViewer:
    """
    This class is intended as a base class and not to be used outside of one of the TrameViewer2D and TrameViewer3D classes.
    """
    def __init__(self, viewer_class, list_of_files=None):
        # Load files and setup the CILViewer
        if list_of_files is None:
            raise AttributeError("list_of_files cannot be None as we need data to load in the viewer!")
        self.list_of_files = list_of_files

        self.default_file = None
        for file_path in self.list_of_files:
            if "head.mha" in file_path:
                self.default_file = file_path
                break
        if self.default_file is None:
            self.default_file = list_of_files[0]

        # Create the relevant CILViewer
        self.cil_viewer = viewer_class()
        self.load_file(self.default_file)

        self.html_view = vtk.VtkRemoteView(self.cil_viewer.renWin)

        # Create page title using the class name of the viewer so it changes based on whatever is passed to this class
        page_title = f"{viewer_class.__name__} on web"
        self.layout = SinglePageWithDrawer(page_title, on_ready=self.html_view.update, width=300)
        self.layout.title.set_text(page_title)
        self.layout.logo.children = [vuetify.VIcon("mdi-skull", classes="mr-4")]

    def start(self):
        self.layout.start()

    def load_file(self, file_name, windowing_method="scalar"):
        if "data" not in file_name:
            file_name = os.path.join("data", file_name)
        if ".nxs" in file_name:
            self.load_nexus_file(file_name)
        else:
            self.load_image(file_name)

    def load_image(self, image_file: str):
        reader = vtkMetaImageReader()
        reader.SetFileName(image_file)
        reader.Update()
        self.cil_viewer.setInput3DData(reader.GetOutput())

    def load_nexus_file(self, file_name):
        reader = cilHDF5ResampleReader()
        reader.SetFileName(file_name)
        reader.SetDatasetName('entry1/tomo_entry/data/data')
        reader.SetTargetSize(256 * 256 * 256)
        reader.Update()
        self.cil_viewer.setInput3DData(reader.GetOutput())
