# 2D Slice Viewer

The 2D slice viewer was designed to quickly visualise and interact with large 3D datasets. There are a number of interactions
which will allow the user to slice through the image on 3 axes, plot a histogram and profile horizontal and vertical cross sections of the image.

## Opening a file
Click the folder icon in the toolbar and select the file to load. This application can load single files or multiple files in tiff format.

## Saving the current image in the 2D slicer
Click the save icon in the toolbar and pick a destination.

## Interactions
Mouse and keyboard interaction for the 2D Slicer.

### 2D Slicer
#### Keyboard Interactions
* x - Slices on the YZ plane
* y - Slices on the XZ plane
* z - Slices on the XY plane
* a - Auto window/level to accomodate all values
* l - Plots horizontal and vertical profiles of the displayed image at the pointer location

#### Mouse Interactions
* Slice Up/Down - Scroll (x10 speed pressing SHIFT)
* Window/Level  - ALT + Right Mouse Button + Drag
* Pan           - CTRL + Right Mouse Button + Drag
* Zoom          - SHIFT + Right Mouse Buttin + Drag (up: zoom in, down: zoom out)
* Pick          - Left Mouse Click
* Region of interest
    * Create ROI    - CTRL + Left Mouse Button
    * Resize ROI    - Click + Drag nodes
    * Translate ROI - Middle Mouse Button within ROI + Drag
    * Delete ROI    - ALT + Left Mouse Button
