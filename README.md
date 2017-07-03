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


