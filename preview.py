#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 30 15:55:22 2017

@author: edo
"""

import numpy as np
import vtk
from ccpi.viewer.CILViewer2D import CILViewer2D
import dxchange

cor = np.double(100)
resolution = 1
niterations = 3
threads = 24

tot_images = 1049
crop = True

## create a reduced 3D stack
nreduced = 3

stack = vtk.vtkImageData()
reader = vtk.vtkTIFFReader()
#directory = "/home/edo/Dataset/20170419_crabtomo/crabtomo"
directory = "D:\\Documents\\Dataset\\IMAT\\20170419_crabtomo\\crabtomo"

for num in range(nreduced):
    img = int(float(num) / float(nreduced) * float(tot_images))
    fn = directory + "\\Sample\\IMAT00005153_crabstomo_Sample_%03d.tif"
    print("resampling %s" % (fn % img))
    reader.SetFileName(fn % img)
    reader.Update()
    if num == 0:
        sliced = reader.GetOutput().GetExtent()
        stack.SetExtent(sliced[0], sliced[1], sliced[2], sliced[3], 0,
                        nreduced - 1)
        size = (sliced[1] + 1) * (sliced[3] + 1) * nreduced
        #stack.SetNumberOfScalarComponents(1)
        stack.AllocateScalars(vtk.VTK_DOUBLE, 1)
        print("Image Size: %d" % ((sliced[1] + 1) * (sliced[3] + 1)))
    dims = reader.GetOutput().GetDimensions()
    for i in range(dims[0]):
        for j in range(dims[1]):
            stack.SetScalarComponentFromDouble(
                i, j, 0, 0,
                reader.GetOutput().GetScalarComponentAsDouble(i, j, num, 0))
#writer = vtk.vtkMetaImageWriter()
#stack.SetOrigin(0,0,0)
#stack.SetSpacing(1,1,1)
#writer.SetInputData(stack)
#writer.SetFileName("datareduced.mha")
#writer.Write()

#fname = "/home/edo/Dataset/20170419_crabtomo/crabtomo/Sample/IMAT00005153_crabstomo_Sample_000.tif"
##ind = [i for i in range(tot_images)]
## reduced dataset
#images = 3
#ind = [int(i*tot_images / images) for i in range(images)]
#stack_image = dxchange.reader.read_tiff_stack(fname, ind, digit=3, slc=None)

v = CILViewer2D()
#v.setInputAsNumpy(stack_image)
v.setInput3DData(stack)
v.displaySlice()

ROI = v.getROI()
print(ROI)

crop = False
if crop:
    # crop images
    reader = vtk.vtkTIFFReader()
    voi = vtk.vtkExtractVOI()
    voi.SetInputData(reader.GetOutput())
    voi.SetVOI(ROI[0][0], ROI[0][1], ROI[1][0], ROI[1][1], 0, 1)
    # makes a square 884x884
    #subsample? 1/4
    voi.SetSampleRate(4, 4, 1)

    writer = vtk.vtkTIFFWriter()
    writer.SetInputData(voi.GetOutput())

    directory = "/home/edo/Dataset/20170419_crabtomo/crabtomo"

    for img in range(tot_images):
        fn = directory + "/Sample/IMAT00005153_crabstomo_Sample_%03d.tif"
        print("resampling %s" % (fn % img))
        reader.SetFileName(fn % img)
        reader.Update()
        voi.Update()
        fn = directory + "/Crop/IMAT00005153_crabstomo_Sample_%03d.tif"
        writer.SetFileName(fn % img)
        writer.Write()

    for img in range(10):
        fn = directory + "/Flat_before/IMAT00005152_crabstomo_Flat_before_%03d.tif"
        print("resampling %s" % (fn % img))
        reader.SetFileName(fn % img)
        reader.Update()
        voi.Update()
        fn = directory + "/Crop/IMAT00005152_crabstomo_Flat_before_%03d.tif"
        writer.SetFileName(fn % img)
        writer.Write()

    for img in range(1, 41):
        fn = directory + "/dark/IMAT00005149_darkafterf123_rep_dk_%03d.tif"
        print("resampling %s" % (fn % img))
        reader.SetFileName(fn % img)
        reader.Update()
        voi.Update()
        fn = directory + "/Crop/IMAT00005149_darkafterf123_rep_dk_%03d.tif"
        writer.SetFileName(fn % img)
        writer.Write()
    ##################
