# Tri Widget Viewer

The tri widget viewer was designed to display 3 different views of the data simultaneously. 
The main element of the viewer is a 2D slicer. Two sub-windows display a 3D slicer and graph.
Generating the graph will also generate surfaces which are rendered in the 3D slicer. 
Interaction with the 2D and 3D slicers can be linked or unlinked depending on user preference.

## Opening a file
Click the folder icon in the toolbar and select the file to load. This application can load single files or multiple files in tiff format.

## Saving the current image in the 2D slicer
Click the save icon in the toolbar and pick a destination.

## Interactions
Mouse and keyboard interaction differ for the different viewers. The 2D Slicer has the most interactions available.

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

### 3D Slicer
#### Keyboard Interactions
* x - Slices on the YZ plane
* y - Slices on the XZ plane
* z - Slices on the XY plane

#### Mouse Interactions
* Adjust Camera - Left Mouse Button + Drag
* Pan           - SHIFT + Left Mouse Button + Drag
* Rotate        - CTRL + Left Mouse Button + Drag
* Zoom          - Right Mouse Button + Drag (up: zoom in, down: zoom out)


### Graph
#### Mouse Interaction
* Zoom          - Scroll
* Pan           - ALT + Left Mouse Button + Drag
* Select Region - Left Mouse Button + Drag
* Pick          - Left Mouse Button


## Generating the graph
The graph can be generated in the graph tools panel. This is opened using the graph icon. ![alt text][graph icon]

Click "Generate Graph" to generate the graph and 3D surfaces. One the graph has been generated, modify the parameters and click "Update" to push the changes to the viewers.

### Parameters

* Iso Value           - As a percentage of the pixel value range, what iso value to calculate the tree and surfaces from.
* Global Iso          - If unchecked, will use local iso-value
* Colour Surfaces     - Colour individual elements of the rendered object
* Log Tree Size       - 
* Collapse Priority   - 

## Linking the viewers

Interactions on the 2D and 3D viewers can be linked. 
The status of the link is shown by the icon on the button in the top left of the 2D and 3D viewers. Toggling the state is achieved by clicking this button.
When the icon is a closed link ![alt text][linked icon] interactions will be passed from one viewer to the other.
When the icon is an open link ![alt text][unlinked icon] interactions will not be passed between the viewers.

If slice actions are performed while the viewers are unlinked, they will become out of sync. If this is undesireable, scroll until both viewers reach the extent
of the current slicing direction and then the slice will be syncronised again.

If window/level actions are performed while the viewer are unlinked, they will become out of sync. If this is undesireable, link and perform a window/level change
action. The levels will synchronise again.

#### Interactions available from both viewers
These actions will be triggered by performing the action in either the 2D or 3D viewer.

* Slice - Change the slice
* x     - Slice in the YZ plane
* y     - Slice in te XZ plane
* z     - slice in the XY plane

#### Interactions only available in 2D viewer
These actions will only be triggered by performing the action in the 2D viewer.

* Window/Level - Adjust the window/level for the image

## Docking/Showing the Graph and 3D slicer 

The 3D slicer and graph widgets can be removed from the main window and resized in order to get a better view of certain elements.
If you have closed either of the windows, they can be brought back by clicking the show icon ![alt text][show icon]

[graph icon]: images/tree_icon.png "This icon opens the graph tool panel"
[linked icon]: images/link.png "This icon shows the viewers are linked"
[unlinked icon]: images/broken_link.png "This icon shows the viewers are un-linked"
[anchor icon]: images/anchor.png "This icon re-docks floating widgets and shows closed widgets"
[show icon]: ./images.show.png "This icon brings closed windows back"