# Slice by slice viewer

To be able to display a huge image data in full scale we could display one slice at a time. 
This would imply that we rely on the data to not be fully loaded in the viewer, rather 
the viewer gets passed a reader and the reader provides the appropriate slice on request. 
This could be achieved with cropped readers.

However, this also requires some changes in the viewer:

1. The viewer assumes that the member `img3D` is a `vtkImageData`
2. `img3D` is then passed as input to a `vtkExtractVOI` filter to create the `vtkSlice` object
that is rendered on the scene
3. The actual slicing is triggered by mouse wheel event, which do the following:
   a. `setActiveSlice` is called with the new slice number that one wants to select. This actually just stores an integer
   in list of length 3. 
   b. `updatePipeline` is called, which in turn calls either `updateImageWithOverlayPipeline` or `updateRectilinearWipePipeline`
   depending on which visualisation mode we are using. Both methods trigger `updateMainVOI` which sets the extent 
   for `vtkExtractVOI` to the slice that we want to show and the appropriate slice is extracted and rendered.

## Possible way forward

If we need to rely on a file reader to render only part of the data we need to be able to pass
a reader output port to the viewer. The viewer should be able to understand if it's passed a 
`vtkImageData` or a reader, and in the latter case modify `img3D` with the slice that's requested.

This requires to make `img3D` a property along these lines

```python

@property
def img3D(self):
    if self._input_reader is None:
        return self._img3D
    else:
        self._input_reader.Update()
        return self._input_reader.GetOutput()
```