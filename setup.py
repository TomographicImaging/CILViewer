# -*- coding: utf-8 -*-
"""
Created on Wed Jun  7 09:57:13 2017

@author: ofn77899
"""

from distutils.core import setup
#from setuptools import setup, find_packages
import os

cil_version=os.environ['CIL_VERSION']
if  cil_version == '':
    print("Please set the environmental variable CIL_VERSION")
    sys.exit(1)

setup(
    name="ccpi-viewer",
    version=cil_version,
    packages=['ccpi','ccpi.viewer'],
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
