from ccpi.viewer.CILViewer2D import CILViewer2D
import vtk

# This example imports a 2D tiff image and tests the 2D viewer
DATASET_TO_READ = [path]  # insert path here
if DATASET_TO_READ is not None:
    reader = vtk.vtkTIFFReader()
    reader.SetFileName(DATASET_TO_READ)
    reader.Update()

    v = CILViewer2D()
    print(reader.GetOutput())
    v.setInputData(reader.GetOutput())
    v.startRenderLoop()