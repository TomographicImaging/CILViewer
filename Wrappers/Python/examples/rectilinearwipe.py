# Example of RectilinearWipe in CILViewer
# freely based on https://kitware.github.io/vtk-examples/site/Cxx/Widgets/RectilinearWipeWidget/
# Author Edoardo Pasca 2021

import vtk
import numpy
import os
from ccpi.viewer.utils.conversion import Converter
from vtk.util import numpy_support , vtkImageImportFromArray

# Utility functions to transform numpy arrays to vtkImageData and viceversa
    
def numpy2vtkImporter(nparray, spacing=(1.,1.,1.), origin=(0,0,0), transpose=[2,1,0]):
    '''Creates a vtkImageImportFromArray object and returns it.
    
    It handles the different axis order from numpy to VTK'''
    importer = vtkImageImportFromArray.vtkImageImportFromArray()
    importer.SetArray(numpy.transpose(nparray, transpose).copy())
    importer.SetDataSpacing(spacing)
    importer.SetDataOrigin(origin)
    return importer

ren = vtk.vtkRenderer()
renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren)
interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(renWin)

# here we load the whole dataset. It may be possible to read only part of it?
data1 = numpy.load(os.path.abspath("C:/Users/ofn77899/Data/dvc/frame_000_f.npy"))
data2 = numpy.load(os.path.abspath("C:/Users/ofn77899/Data/dvc/frame_010_f.npy"))
img1 = Converter.numpy2vtkImage(data1, deep = 0)
img2 = Converter.numpy2vtkImage(data2, deep = 1)

reader1 = vtk.vtkExtractVOI()
reader2 = vtk.vtkExtractVOI()

reader1.SetInputData(img1)
reader2.SetInputData(img2)

extent1 = list(img1.GetExtent())
extent2 = list(img2.GetExtent())
#extent is slice number N
N1 = 512
extent1[4] = N1
extent1[5] = N1
extent2[4] = N1
extent2[5] = N1

reader1.SetVOI(*extent1)
reader2.SetVOI(*extent2)
# img1 = numpy.expand_dims(data[512], axis=0)

# reader1 = numpy2vtkImporter(img1, transpose=[0,1,2])
# # img1 = Converter.numpy2vtkImage(tmp, deep=1)

# img2 = numpy.expand_dims(data[612], axis=0)
# reader2 = numpy2vtkImporter(img2, transpose=[0,1,2])
# img2 = Converter.numpy2vtkImage(tmp, deep=1)

wipe = vtk.vtkImageRectilinearWipe()
wipe.SetInputConnection(0, reader1.GetOutputPort())
wipe.SetInputConnection(1, reader2.GetOutputPort())
wipe.SetPosition(256,256)
wipe.SetWipe(0)


wipeActor = vtk.vtkImageActor()
wipeActor.GetMapper().SetInputConnection(wipe.GetOutputPort())

wipeWidget = vtk.vtkRectilinearWipeWidget()
wipeWidget.SetInteractor(interactor)

wipeWidgetRep = wipeWidget.GetRepresentation()
wipeWidgetRep.SetImageActor(wipeActor)
wipeWidgetRep.SetRectilinearWipe(wipe)
wipeWidgetRep.GetProperty().SetLineWidth(2.0)
wipeWidgetRep.GetProperty().SetOpacity(0.75)

ren.AddActor(wipeActor)
renWin.SetSize(512,512)

renWin.Render()
wipeWidget.On()
interactor.Start()


