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
import subprocess


cil_version = subprocess.check_output('git describe', shell=True).decode("utf-8").rstrip()


if os.environ.get('CONDA_BUILD', 0) == '1':
    cwd = os.getcwd()
    # requirements are processed by conda
    requires = []
else:
    requires = ['numpy','vtk']
    cwd = os.path.join(os.environ.get('RECIPE_DIR'),'..')

# update the version string
fname = os.path.join(cwd, 'ccpi', 'viewer', 'version.py')

if os.path.exists(fname):
    os.remove(fname)
with open(fname, 'w') as f:
    f.write('version = \'{}\''.format(cil_version))
    

setup(
    name="ccpi-viewer",
    version=cil_version,
    packages=['ccpi','ccpi.viewer', 'ccpi.viewer.utils'],
	install_requires=requires,
    zip_safe = False,
    # metadata for upload to PyPI
    author="Edoardo Pasca",
    author_email="edoardo.pasca@stfc.ac.uk",
    description='CCPi CILViewer',
    license="Apache v2.0",
    keywords="3D data viewer",
    url="http://www.ccpi.ac.uk",   # project home page, if any

    # could also include long_description, download_url, classifiers, etc.
)
