# -*- coding: utf-8 -*-
"""
Created on Tue Jun 20 12:57:08 2017

@author: ofn77899
"""

from edo import CILViewer
import numpy
import vtk
from vtk.util import numpy_support

def readAs3DNumpyArray(filename):
    reader = vtk.vtkVolume16Reader()
    reader.SetDataDimensions (64,64)
    reader.SetImageRange(1,93)
    reader.SetDataByteOrderToLittleEndian()
    reader.SetFilePrefix(filename)
    reader.SetDataSpacing (3.2, 3.2, 1.5)
    reader.Update()
    # transform the VTK data to 3D numpy array
    img_data = numpy_support.vtk_to_numpy(
        reader.GetOutput().GetPointData().GetScalars())

    data3d = numpy.reshape(img_data, reader.GetOutput().GetDimensions())
    return (data3d , reader)


# 2. Pass data into the segmentor
# load data with vtk
filename = "C:\\Users\\ofn77899\\Documents\\GitHub\\VTKData\\Data\\headsq\\quarter"

# read the data as 3D numpy array
data3d , reader = readAs3DNumpyArray(filename)

viewer = CILViewer()
#viewer.setInputAsNumpy(data3d)
viewer.setInput3DData(reader.GetOutput())

viewer.displaySliceActor(0)
viewer.startRenderLoop()