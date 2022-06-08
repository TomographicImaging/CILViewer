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
from trame.html import vuetify

from ccpi.viewer.CILViewer2D import CILViewer2D
from ccpi.web_viewer.trame_viewer import TrameViewer


class TrameViewer2D(TrameViewer):
    def __init__(self, list_of_files=None):
        super().__init__(list_of_files=list_of_files, viewer_class=CILViewer2D)

        self.create_drawer_ui_elements()

        self.construct_drawer_layout()

        self.layout.children += [
            vuetify.VContainer(
                fluid=True,
                classes="pa-0 fill-height",
                children=[self.html_view],
            )
        ]

    def construct_drawer_layout(self):
        pass

    def create_drawer_ui_elements(self):
        pass
