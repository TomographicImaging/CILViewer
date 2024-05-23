# Changelog

## v24.0.0

New functionality:
- Add method to edit axes label text & tests, hide one label on 2D viewer #389 #408
- Add slider widget #365 and option to not install it #386
- adds Qt GUI toolbar to control 3D viewer

Bugfixes:
- Fix failing unit test #394
- Bugfix on resample reader #359. Standalone viewer app defaults to downsample in all dimensions.
- Fix bug with setInputAsNumpy() using deprecated `numpy2vtkImporter` in `CILViewer2D` - now uses `numpy2vtkImage`

CI:
- Update eqt requirements to >=1.0.0 and update yml recipe #385
- Remove VTK 8 variants from conda recipe.
- Change Python variants: removed 3.6 and 3.7, added 3.11 
 (not Python 3.12 for incompatibility with EQT #399)
- Removed the `paskino` channel from the install command as eqt is on `conda-forge`

Documentation
- Add CONTRIBUTING.md #403
- Edit web-viewer readme #401
- Transfer repository to "TomographicImaging" #402


## v23.1.0
- Raise error if try to add multiple widgets with the same name to CILViewer or CILViewer2D.
- Adds the following base classes to `ui.main_windows.py`:
  - Add `ViewerMainWindow` and `ViewerMainWindowWithSessionManagement` - base classes for windows which would house viewers, with methods needed for creating settings dialogs, creating a coordinate settings dockwidget, and loading images.
  - Add `TwoViewersMainWindow` and `TwoViewersMainWindowWithSessionManagement` - baseclasses which create a main window with 2 linked viewers in dockwidgets.
  - `TwoViewersMainWindowMixin` - a mixin which provides methods to both `TwoViewersMainWindowWithSessionManagement` and `TwoViewersMainWindow`. These methods are for adding viewers to the window, setting them up, linking them and adding a dockwidget for coordinate settings.
- Adds the following dialogs to `ui.dialogs.py`:
  - `ViewerSettingsDialog` - allows user to set downsample size settings and whether to use GPU for volume render.
  - `RawInputDialog` - for setting info for loading a raw file including, size of dimensions, data type etc.
  - `HDF5InputDialog` - for setting info for loading a HDF5 file, including the dataset name
  - Unit tests for creating each dialog.
  Adds the following widgets to `ui.qt_widgets.py`:
  - `ViewerCoordsDockWidget` - for showing original and downsampled image size and allowing user to select which coord system to show on viewer.
- Adds a `cilviewer` entrypoint:
 - This launches a standalone viewer application with a 2D and 3D viewer and allows users to load any image file types we support using the File menu.
 - This launches a `StandaloneViewer` instance (`standalone_viewer.py`)
- Updates README with how to run standalone viewer app and web viewer, and more image examples
- Adds methods to `CILViewerBase`:
 - `setVisualisationDownsampling` (moved out of CILViewer2D)
 - `getVisualisationDownsampling` (moved out of CILViewer2D)
- Adds methods to `CILViewer`:
  - `setVolumeMapper`
  - `getVolumeMapper`
- Modifies `ImageReader`:
  - Previously could read only from a file, now can read from memory instead by setting `vtk_image` parameter instead of `file_name` parameter.
  - Add `SetVTKImage` method
  - Added unit tests to cover providing a VTK image instead of file name
- Add methods to `cilviewerHDF5Reader`:
  - GetOriginalImageAttrs
  - GetLoadedImageAttrs
  - These methods are the same as those in `ImageReader` to be consistent.

## v23.0.0
- add `deleteWidget` method to CILViewerBase
- Add environment file for development of the viewer
- ImageWriter writes out with file extension set in FileFormat variable - previously didn't necessarily
  do this for some hdf5 formats.
- Fix bug with returning HDF5 attributes from HDF5Reader
- Move code for resetting camera out of TrameViewer3D and into CILViewer
- Adds the following methods to CILViewer (and corresponding unit tests):
    - getGradientOpacityPercentiles
    - getScalarOpacityPercentiles
    - getVolumeColorPercentiles
- Adds to CILViewerBase (and corresponding unit tests):
    - getSliceColorPercentiles
- setup.py:
  - Always normalise the version from git describe to pep440

## v22.4.0
- Add command line tool for resampling a dataset, with entrypoint: resample (and unit tests)
- Add `ImageReader`: 
  - Generic reader for reading to vtkImageData
  - Reads: HDF5, MetaImage, Numpy, Raw, TIFF stacks
  - Supports resampling OR cropping the dataset whilst reading.
- Add `ImageWriter`:
  - Writer for writing out a modified i.e. resampled or cropped dataset.
  - Supports writing to HDF5 and metaimage.
- Add `ImageWriterInterface`:
  - Interface for writers, with methods for setting and getting information about modified
    (i.e. resampled or cropped) image data to write to a file.
- Add `cilviewerHDF5Writer`:
  - This is a writer which expects to be writing an original dataset or attributes of the original dataset, 
  plus one or more 'child' versions of the dataset which have been resampled and/or cropped.
  - Stores the information needed to reload a resampled or cropped dataset on the viewer.
- Add `cilviewerHDF5Reader`:
  - for reading datasets generated by the cilviewerHDF5Writer.
- Add new requirements:
  - `schema`
  - `pyyaml`
- Examples:
  - `examples/image_reader_and_writer.py` is an example of using the `ImageReader` and `ImageWriter`
  - `examples/opacity_in_viewer.py` updated to use head dataset from `utils/example_data.py`
- Unit tests for all of the new readers and writers.
- Removed obsolete TIFF code from conversion.py. The following have been removed:
  - `vtkTiffStack2numpy`
  - `tiffStack2numpy`
  - `tiffStack2numpyEnforceBounds`
  - `_tiffStack2numpy`
  - `normalize`
  - `highest_tuple_element`
- Fixed cilTIFFResampler so that if original TIFF file has a set spacing and origin, this is taken into account when resampling.
- Fixed bug in `iviewer` with display of volume render.
- iviewer now shows gradient opacity volume render of head dataset from `utils/example_data.py` by default.
- Fix bug in CILViewer if volume render method is adjusted before volume render turned on.

## v22.3.0
- Add a dictionary of widgets to the CILViewerBaseClass, and ability to add and retrieve widgets to/from the dict with methods `.addWidgetReference` and `.getWidget`
- Add a new file widgets/box_widgets.py which contains classes cilviewerBoxWidget and cilviewerLineWidget for creating Box and Line widgets on the viewer.
- Add example: BoxWidgetAroundSlice.py - which demonstrates using the above classes.
- Use the cilviewerBoxWidget class for creating and positioning the ROIWidget on the CILViewer2D, which involved removing the `CILViewer2D._truncateBox` method.
- Conda recipe:
  - Add build variants for python. 

## v22.2.0
- Qt examples use example_data 
- Updates in all classes to take into account the backward incompatible methods name changes (see below)
- cilPlaneClipper: 
  - change signature of creator, and defaults to empty list of items to be clipped on init
  - renamed Get/SetInteractor->Get/SetInteractorStyle
- Renamed all classes bearing name baseReader to ReaderInterface as they provide the interface not a abstract reader class.
- Added TIFF resample and cropped readers with unit tests.
- Add Set/GetOrientationType methods to TIFF resample and cropped readers, with default value 1: ORIENTATION_TOPLEFT (row 0 top, col 0 lhs)
- web_viewer:
  - added web viewer using trame for viewer3D and viewer2D
  - add entry point for running the web viewers
  - added docker container to be deployed
- GitHub Action: autoyapf added
- Added example_data module to load the head data from the CIL-Data repository
- CILViewer2D: 
  - add ChangeOrientation, AutoWindowLevel, getSliceWindowLevelFromRange
  - Backward incompatible rename of a few methods: 
    - Get/SetActiveSlice -> get/setActiveSlice, 
    - GetSliceOrientation -> getSliceOrientation, 
    - setColourWindowLevel -> setSliceColorWindowLevel, 
    - getColourLevel -> getSliceColourLevel, 
    - getColourWindow -> getSliceColorWindow, 
    - setColourWindowLevel -> setSliceColorWindowLevel
  - fix definition of window range to be = max - min
  - use CILViewerBase as base class
- CILViewer3D:
  - added methods in interactor style to enable interaction with web app, rather than just key event binding
  - add volume render opacity scalar and gradient
  - add slice histogram
  - fix method to change window and level for slice actor, by range or percentiles
  - fix definition of window range to be = max - min
  - use CILViewerBase as base class
- colormaps: added get_color_transfer_function
- added examples of running the 2D and 3D viewers without Qt
- Added CILViewer base class
- Conda recipe:
  - Fix windows build recipe
  - Add build variants for VTK to prevent need for multiple viewer release numbers for different VTK versions

## v22.1.2
* Changes released in 22.0.2, but also requires vtk version >= 9.0.3

## v22.0.2
* requires vtk 8.1.2
* When a new image is loaded on the 3D viewer, reset camera position, slice and volume orientation and visibility, and clipping planes.
* Fix downsampling of resample readers when working with datatypes other than uint8. Previously resulting size of image was multiple times greater than requested target size as uint8 type was always assumed.

## v22.1.1
* Changes released in 22.0.1, but also requires vtk version >= 9.0.3

## v22.0.1
* requires vtk 8.1.2
* Fixes enabling and disabling slice with 's' key in 3D viewer
* Adds widget for slicing a volume with the 'c' key in the 3D viewer
* Add light to 3D viewer
* Add a few utility methods for volume rendering in 3D viewer
* Create utils/io.py with code to save current render as PNG
* Increments number in name of file when saving render to PNG, so multiple captures can be made without them overwriting each other.
* Add vtkImageResampler, which downsamples from memory
* When a new 3D image is input, volume render is updated and clipping planes are cleared
* No need to specify VTK array name when writing to HDF5
* Allow setting both 4D index and 4D slice index when reading 4D HDF5 dataset

## v22.1.0
* requires vtk version >= 9.0.3

## v22.0.0
* requires vtk 8.1.2
* Adds HDF5Reader for reading of HDF5 files to vtkImageData, and RequestSubset reads a cropped version of the image
* Adds write_image_data_to_hdf5 which writes vtkImageData to HDF5 files
* Resampling of HDF5 with cilHDF5ImageResampleReader
* Unit tests of the new HDF5 methods
* Add unit test for importing version number
* set package as noarch and remove variants as not strictly depending on versions of python or numpy
* Use vtkImageSlice instead of vtkImageActor and vtkImageMapToWindowLevelColor in the 2D and 3D viewers
* Update viewer so it can work with vtk9
* Adds new mode of visualisation that allows the comparison of 2 equally shaped/spaced images with a rectilinear wipe. The visualisation with the wipe can be triggered by typing key 2 and reset to normal (image with overlay) by key 1.
* Adds cilHDF5CroppedReader
* Fix bug in cropped readers which was causing a warning about the incorrect number of bytes being read from a metaimage file
* Moves functionality for reading raw images out of the base classes for cropped and resample readers
* Restructures readers to have a base class for each filetype we read so that methods are shared between the cropped readers and resample readers
* Improved error reporting in resample and cropped readers
* Adds ErrorObserver and EndObserver for handling errors in our readers
* removed the io.py file with the class ImageDataCreator

## v21.1.2
* Fix the setting of the view up vector in the y direction, to avoid getting vtk warning messages.
* The event triggered by the "w" key, (i.e. update the window level) is now based on a smaller area of the image under the cursor. The area is 10% in each direction of the whole image extent.
* The auto window level now uses the average value between 1 and 99 percentile as level and the difference for window. Before it was the median.
* Update examples to use PySide2 instead of PyQt5 

## v21.1.1
* fix bug with importing version number

## v21.1.0
* infer the version string from the repository tag
* fix bug with orientation axes when the input image is updated
* Allow colormap to be changed in the 3D viewer to any colormap available in matplotlib

## v21.0.1
* change default orientation of axes
* reduce print-outs from code


## v21.0.0

 * change backend for Qt as PySide2

 * Fix definition of image and world coords

 * Update corner annotation to use new definition
 
 * Fix origin of resampled image to use new coordinate definition

 * Make use of original image origin and spacing when downsampling and cropping images

 * Change default raw datatype to be unit8
