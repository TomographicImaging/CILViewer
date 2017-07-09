#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  4 14:41:44 2017

@author: edo
"""

import numpy as np
from vtk.util import numpy_support
from vtk.util import vtkImageImportFromArray


def numpy2vtkImporter(nparray, spacing=(1.,1.,1.), origin=(0,0,0)):
    importer = vtkImageImportFromArray.vtkImageImportFromArray()
    importer.SetArray(np.transpose(nparray).copy())
    importer.SetDataSpacing(spacing)
    importer.SetDataOrigin(origin)
    return importer

def numpy2vtk(nparray, spacing=(1.,1.,1.), origin=(0,0,0)):
    importer = numpy2vtkImporter(nparray, spacing, origin)
    importer.Update()
    return importer.GetOutput()

def vtk2numpy(imgdata):
    # transform the VTK data to 3D numpy array
    img_data = numpy_support.vtk_to_numpy(
            imgdata.GetPointData().GetScalars())

    dims = imgdata.GetDimensions()
    dims = (dims[2],dims[1],dims[0])
    data3d = np.reshape(img_data, dims)
    
    return np.transpose(data3d).copy() 

A = np.asarray([i for i in range(4*3*5)], dtype=np.float32)

A = np.reshape(A, (3,4,5))

#vtkImg = numpy2VTK(A)
dim = A.shape
spacing=[1.0, 1.0, 1.0]

vtkdata = numpy2vtk(A)

B = vtk2numpy(vtkdata)

for i in range(dim[0]):
    for j in range(dim[1]):
        for k in range(dim[2]):
            print("_______________________________________________")
            print ("Numpy slice A[%d][%d][%d] %d " % (i,j,k,A[i][j][k]))
            print ("VTK GetComponent %d %d %d %d " % (i,j,k,vtkdata.GetScalarComponentAsDouble(i,j,k,0)))
            print ("Numpy slice B[%d][%d][%d] %d " % (i,j,k,B[i][j][k]))
            


#tot_len = np.shape(A)[0] * np.shape(A)[1] * np.shape(A)[2]
#
#doubleImg = vtk.vtkImageData()
#shape = np.shape(A)
#doubleImg.SetDimensions(shape[0], shape[1], shape[2])
#doubleImg.SetOrigin(0,0,0)
#doubleImg.SetSpacing(1,1,1)
#doubleImg.SetExtent(0, shape[0]-1, 0, shape[1]-1, 0, shape[2]-1)
##self.img3D.SetScalarType(vtk.VTK_UNSIGNED_SHORT, vtk.vtkInformation())
#doubleImg.AllocateScalars(vtk.VTK_UNSIGNED_SHORT,1)
#
##vtkimg = numpy_support.numpy_to_vtk(np.reshape(A,(tot_len,)), deep=True, array_type=vtk.VTK_UNSIGNED_SHORT)
#
##doubleImg.GetData()
