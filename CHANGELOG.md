# Changelog

## v***
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
