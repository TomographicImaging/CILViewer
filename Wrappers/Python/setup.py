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

from setuptools import setup
import os
import sys
import subprocess


def version2pep440(version):
    '''normalises the version from git describe to pep440
    
    https://www.python.org/dev/peps/pep-0440/#id29
    '''
    if version[0] == 'v':
        version = version[1:]

    if u'-' in version:
        v = version.split('-')
        v_pep440 = "{}.dev{}".format(v[0], v[1])
    else:
        v_pep440 = version

    return v_pep440


git_version_string = subprocess.check_output('git describe', shell=True).decode("utf-8").rstrip()[1:]

if os.environ.get('CONDA_BUILD', 0) == '1':
    cwd = os.path.join(os.environ.get('RECIPE_DIR'), '..')
    # requirements are processed by conda
    requires = []
    version = git_version_string
else:
    requires = ['numpy', 'vtk']
    cwd = os.getcwd()
    version = version2pep440(git_version_string)

# update the version string
fname = os.path.join(cwd, 'ccpi', 'viewer', 'version.py')

if os.path.exists(fname):
    os.remove(fname)
with open(fname, 'w') as f:
    f.write('version = \'{}\''.format(version))

setup(
    name="ccpi-viewer",
    version=version,
    packages=['ccpi', 'ccpi.viewer', 'ccpi.viewer.utils'],
    install_requires=requires,
    zip_safe=False,
    # metadata for upload to PyPI
    author="Edoardo Pasca",
    author_email="edoardo.pasca@stfc.ac.uk",
    description='CCPi CILViewer',
    license="Apache v2.0",
    keywords="3D data viewer",
    url="http://www.ccpi.ac.uk",  # project home page, if any

    # could also include long_description, download_url, classifiers, etc.
)
