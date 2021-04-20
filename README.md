| Master | Development | Anaconda binaries |
|--------|-------------|-------------------|
| [![Build Status](https://anvil.softeng-support.ac.uk/jenkins/buildStatus/icon?job=CILsingle/CCPi-Viewer)](https://anvil.softeng-support.ac.uk/jenkins/job/CILsingle/job/CCPi-Viewer/) | [![Build Status](https://anvil.softeng-support.ac.uk/jenkins/buildStatus/icon?job=CILsingle/CCPi-Viewer-dev)](https://anvil.softeng-support.ac.uk/jenkins/job/CILsingle/job/CCPi-Viewer-dev/) |![conda version](https://anaconda.org/ccpi/ccpi-viewer/badges/version.svg) ![conda last release](https://anaconda.org/ccpi/ccpi-viewer/badges/latest_release_date.svg) [![conda platforms](https://anaconda.org/ccpi/ccpi-viewer/badges/platforms.svg) ![conda dowloads](https://anaconda.org/ccpi/ccpi-viewer/badges/downloads.svg)](https://anaconda.org/ccpi/ccpi-viewer) |

# CILViewer
A simple Viewer for 3D data built with VTK and Python.

The interactive viewer CILViewer2D provides:

  - Orthoslicer (slice in x/y/z direction)
  - keyboard interaction
    - 'x' slices on the YZ plane
    - 'y' slices on the XZ plane
    - 'z' slices on the XY
    - 'a' auto window/level to accomodate all values
    - 's' save render to PNG (current_render.png)
    - 'l' plots horizontal and vertical profiles of the displayed image at the pointer location
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

![Window/Level](pics/windowLevel.png)
![Zoom](pics/zoom.png)
![Slice X + Pick](pics/sliceXPick.png)
![ROI](pics/ROI.png)
![line](pics/line.png)

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
