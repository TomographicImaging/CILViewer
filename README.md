| Master | Development | Anaconda binaries |
|--------|-------------|-------------------|
| [![Build Status](https://anvil.softeng-support.ac.uk/jenkins/buildStatus/icon?job=CILsingle/CCPi-Viewer)](https://anvil.softeng-support.ac.uk/jenkins/job/CILsingle/job/CCPi-Viewer/) | [![Build Status](https://anvil.softeng-support.ac.uk/jenkins/buildStatus/icon?job=CILsingle/CCPi-Viewer-dev)](https://anvil.softeng-support.ac.uk/jenkins/job/CILsingle/job/CCPi-Viewer-dev/) |![conda version](https://anaconda.org/ccpi/ccpi-viewer/badges/version.svg) ![conda last release](https://anaconda.org/ccpi/ccpi-viewer/badges/latest_release_date.svg) [![conda platforms](https://anaconda.org/ccpi/ccpi-viewer/badges/platforms.svg) ![conda downloads](https://anaconda.org/ccpi/ccpi-viewer/badges/downloads.svg)](https://anaconda.org/ccpi/ccpi-viewer) |

# CILViewer
A simple Viewer for 3D data built with VTK and Python.
There are two versions:
- GUI built with Python Qt
- Web viewer, built with trame
The viewers can also be embedded into any Qt application.
An example of use of the viewers in another app is the [iDVC app](https://github.com/TomographicImaging/iDVC)

## Install instructions
To install via `conda`, create a new environment using:

```bash
conda create --name cil-viewer -c ccpi -c paskino -c conda-forge"
```

## Running the CILViewer app

- Activate your environment using: ``conda activate cil-viewer``.
- Launch by typing: `cilviewer`
- Load a dataset using the File menu. Currently supported data formats:
  - HDF5, including Nexus
  - Raw
  - Tiff
  - Numpy
  - Metaimage (mha and mhd)

## Web viewer
See [here](https://github.com/vais-ral/CILViewer/tree/master/Wrappers/Python/ccpi/web_viewer) for instructions on how to install and run the web viewer.

## Using the 2D and 3D Viewers

### **2D Viewer**
### Keybindings
The interactive viewer CILViewer2D provides:
  - Keyboard Interactions:
    - 'h' display the help
    - 'x' slices on the YZ plane
    - 'y' slices on the XZ plane
    - 'z' slices on the XY
    - 'a' auto window/level to accomodate all values
    - 's' save render to PNG (current_render.png)
    - 'l' plots horizontal and vertical profiles of the displayed image at the pointer location
    - 'i' toggles interpolation
  - slice up/down: mouse scroll (10 x pressing SHIFT)
  - Window/Level: ALT + Right Mouse Button + drag
  - Pan: CTRL + Right Mouse Button + drag
  - Zoom: SHIFT + Right Mouse Button + drag (up: zoom in, down: zoom out)
  - Pick: Left Mouse Click
  - ROI (square): 
    - Create ROI: CTRL + Left Mouse Button 
    - Resize ROI: Left Mouse Button on outline + drag
    - Translate ROI: Middle Mouse Button within ROI
    - Delete ROI: ALT + Left Mouse Button

### Examples

| Head Dataset	| Zoom 	| Slice X + Pick 	|
|-----	|---	|---	|
|![Window/Level](pics/windowLevel.png)|![Zoom](pics/zoom.png)|![Slice X + Pick](pics/sliceXPick.png)|

| ROI | Line profiles |
|---	|---	|
|![ROI](pics/ROI.png)|![line](pics/line.png)|

### **3D Viewer**
### Keybindings
The interactive 3D viewer CILViewer provides:
  - Keyboard Interactions:
    - 'h' display the help
    - 'x' slices on the YZ plane
    - 'y' slices on the XZ plane
    - 'z' slices on the XY
    - 'r' save render to current_render.png
    - 's' toggle visibility of slice
    - 'v' toggle visibility of volume render\n"
    - 'c' activates volume render clipping plane widget, for slicing through a volume.
    - 'a' whole image Auto Window/Level on the slice.
    - 'i' interpolation of the slice.
  - Slice: Mouse Scroll\n"
  - Zoom: Right Mouse + Move Up/Down\n"
  - Pan: Middle Mouse Button + Move or Shift + Left Mouse + Move
  - Adjust Camera: Left Mouse + Move
                             "  - Rotate: Ctrl + Left Mouse + Move\n"
                             "\n"
                             "Keyboard Interactions:\n"
                             "\n"
                             "h: Display this help\n"
                             "x:  YZ Plane\n"
                             "y:  XZ Plane\n"
                             "z:  XY Plane\n"
      ne widget\n"
                             "\n

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





## Install the demos locally



where,

```astra-toolbox``` will allow you to use CIL with the [ASTRA toolbox](http://www.astra-toolbox.com/) projectors (GPLv3 license).

```tigre``` will allow you to use CIL with the [TIGRE](https://github.com/CERN/TIGRE) toolbox projectors (BSD license).

```ccpi-regulariser``` will give you access to the [CCPi Regularisation Toolkit](https://github.com/vais-ral/CCPi-Regularisation-Toolkit).

```tomophantom``` [Tomophantom](https://github.com/dkazanc/TomoPhantom) will allow you to generate phantoms to use as test data.

```cudatoolkit``` If you have GPU drivers compatible with more recent CUDA versions you can modify this package selector (installing tigre via conda requires 9.2).

```ipywidgets``` will allow you to use interactive widgets in our jupyter notebooks.

### Dependency Notes

CIL's [optimised FDK/FBP](https://github.com/TomographicImaging/CIL/discussions/1070) `recon` module requires:
1. the Intel [Integrated Performance Primitives](https://www.intel.com/content/www/us/en/developer/tools/oneapi/ipp.html#gs.gxwq5p) Library ([license](https://www.intel.com/content/dam/develop/external/us/en/documents/pdf/intel-simplified-software-license-version-august-2021.pdf)) which can be installed via conda from the `intel` [channel](https://anaconda.org/intel/ipp).
2. [TIGRE](https://github.com/CERN/TIGRE), which can be installed via conda from the `ccpi` channel.

## Run the demos locally

- Activate your environment using: ``conda activate cil-demos``.

- Clone the ``CIL-Demos`` repository and move into the ``CIL-Demos`` folder.

- Run: ``jupyter-notebook`` on the command line.

- Navigate into ``demos/1_Introduction``

The best place to start is the ``01_intro_walnut_conebeam.ipynb`` notebook.
However, this requires installing the walnut dataset.

To test your notebook installation, instead run ``03_preprocessing.ipynb``, which uses a dataset shipped with CIL, which will
have automatically been installed by conda.

Instead of using the ``jupyter-notebook`` command, an alternative is to run the notebooks in ``VSCode``.


## Advanced Demos

For more advanced general imaging and tomography demos, please visit the following repositories:

* [**Core Imaging Library part I: a versatile python framework for tomographic imaging**](https://github.com/TomographicImaging/Paper-2021-RSTA-CIL-Part-I)

* [**Core Imaging Library part II: multichannel reconstruction
for dynamic and spectral tomography**](https://github.com/TomographicImaging/Paper-2021-RSTA-CIL-Part-II).

