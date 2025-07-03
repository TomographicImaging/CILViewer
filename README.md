| Master | Development | Anaconda binaries |
|--------|-------------|-------------------|
| [![Build Status](https://anvil.softeng-support.ac.uk/jenkins/buildStatus/icon?job=CILsingle/CCPi-Viewer)](https://anvil.softeng-support.ac.uk/jenkins/job/CILsingle/job/CCPi-Viewer/) | [![Build Status](https://anvil.softeng-support.ac.uk/jenkins/buildStatus/icon?job=CILsingle/CCPi-Viewer-dev)](https://anvil.softeng-support.ac.uk/jenkins/job/CILsingle/job/CCPi-Viewer-dev/) |![conda version](https://anaconda.org/ccpi/ccpi-viewer/badges/version.svg) ![conda last release](https://anaconda.org/ccpi/ccpi-viewer/badges/latest_release_date.svg) [![conda platforms](https://anaconda.org/ccpi/ccpi-viewer/badges/platforms.svg) ![conda downloads](https://anaconda.org/ccpi/ccpi-viewer/badges/downloads.svg)](https://anaconda.org/ccpi/ccpi-viewer) |

# CILViewer
A simple interactive viewer based on VTK classes and written in Python.
- The classes in [`viewer`](Wrappers/Python/ccpi/viewer/) define generic viewers that can be embedded in [Qt](https://www.qt.io/) or other user interfaces. [`CILViewer2D`](Wrappers/Python/ccpi/viewer/CILViewer2D.py) is a 2D viewer and [`CILViewer`](Wrappers/Python/ccpi/viewer/CILViewer.py) is a 3D viewer. 
- The classes in [`web viewer`](Wrappers/Python/ccpi/web_viewer/) define a viewer embedded in [trame](https://kitware.github.io/trame/).

Examples of QApplications are the [`iviewer`](Wrappers/Python/ccpi/viewer/iviewer.py) and the [`standalone viewer`](Wrappers/Python/ccpi/viewer/standalone_viewer.py). An example of use in an external software is [iDVC](https://github.com/TomographicImaging/iDVC).

## Installation instructions
To install via `conda`, create a **minimal** environment using:

```bash
conda create --name cilviewer ccpi-viewer=24.0.1 -c ccpi -c conda-forge
```
### Qt embedding

To embed the viewer in Qt applications we provide extra [UI utilities](Wrappers/Python/ccpi/viewer/ui). To use those, the environment needs to include the extra requirements `eqt>=2.0.0` and one Python-Qt binding, such as `PySide2`, `PySide6` or `PyQt5`. The [UI examples](Wrappers/Python/examples/ui_examples) require `cil-data` as well. 

The environment can be updated to include these (`pyside2`) dependencies as follows:
```sh
conda env update --name cilviewer --file Wrappers/Python/conda-recipe/ui_env.yml
```

## Run the standalone viewer QApplication

- Activate your environment using: ``conda activate cilviewer``.
- Launch by typing: `cilviewer`
- Load a dataset using the File menu. Currently supported data formats:
  - HDF5, including Nexus
  - Raw
  - Tiff
  - Numpy
  - Metaimage (mha and mhd)

<img src="Documentation/readme-images/StandaloneViewerEgg.PNG" alt="Your image title" width="500"/>

Data shown is [1].

## Install and run the trame web viewer
Follow the [instructions](https://github.com/vais-ral/CILViewer/tree/master/Wrappers/Python/ccpi/web_viewer) to install and run the web viewer.

<img src="Documentation/readme-images/WebCILViewer3D.PNG" alt="Your image title" width="500"/>

Data shown is [2].

## Documentation
More information on how to use the viewer can be found in [Documentation.md](./Documentation/documentation.md).

## Developer Contribution Guide
We welcome contributions. Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidance.

## Notice
The CIL Viewer code took initial inspiration from a previous project of Edoardo Pasca and Lukas Batteau [PyVE](https://sourceforge.net/p/pyve/code/ci/master/tree/PyVE/), the license of which we report here:

```
Copyright (c) 2012, Edoardo Pasca and Lukas Batteau
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, 
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list
of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this 
list of conditions and the following disclaimer in the documentation and/or other
materials provided with the distribution.

* Neither the name of Edoardo Pasca or Lukas Batteau nor the names of any 
contributors may be used to endorse or promote products derived from this 
software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT 
SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, 
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED 
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR 
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## References
[1] The chocolate egg dataset shown in above examples is dataset `egg2`:

Jakob Sauer Jørgensen, Martin Skovgaard Andersen, & Carsten Gundlach. (2021). HDTomo TXRM micro-CT datasets [Data set]. Zenodo. https://doi.org/10.5281/zenodo.4822516

[2] The head dataset is avaiable in [CIL-Data as 'head.mha'](https://github.com/TomographicImaging/CIL-Data) along with its license.

