# -*- coding: utf-8 -*-
#   Copyright 2017 Edoardo Pasca
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

from distutils.core import setup
import os
import sys

cil_version = "21.1.0"
if os.environ.get('CONDA_BUILD', None) is not None:
    requires = []
else:
    requires = ['numpy','vtk']

setup(
    name="ccpi-viewer",
    version=cil_version,
    packages=['ccpi','ccpi.viewer', 'ccpi.viewer.utils'],
	install_requires=requires,
    zip_safe = False,
    # metadata for upload to PyPI
    author="Edoardo Pasca",
    author_email="edo.paskino@gmail.com",
    description='CCPi Core Imaging Library - VTK Viewer Module',
    license="Apache v2.0",
    keywords="3D data viewer",
    url="http://www.ccpi.ac.uk",   # project home page, if any

    # could also include long_description, download_url, classifiers, etc.
)
