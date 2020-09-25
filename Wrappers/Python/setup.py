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
"""
Created on Wed Jun  7 09:57:13 2017

@author: ofn77899
"""

from distutils.core import setup
#from setuptools import setup, find_packages
import os
import sys

cil_version = "20.07.5"

setup(
    name="ccpi-viewer",
    version=cil_version,
    packages=['ccpi','ccpi.viewer', 'ccpi.viewer.utils'],
	install_requires=['numpy','vtk'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    #install_requires=['docutils>=0.3'],

#    package_data={
#        # If any package contains *.txt or *.rst files, include them:
#        '': ['*.txt', '*.rst'],
#        # And include any *.msg files found in the 'hello' package, too:
#        'hello': ['*.msg'],
#    },
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
