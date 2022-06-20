# Changelog

## v22.x.x
- Renamed all classes bearing name baseReader to ReaderInterface as they provide the interface not a abstract reader class.
- Added TIFF resample reader

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
