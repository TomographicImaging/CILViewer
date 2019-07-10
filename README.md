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
