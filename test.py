# -*- coding: utf-8 -*-
"""
Created on Wed Jun 28 14:23:42 2017

@author: ofn77899
"""

from ccpi.viewer.CILViewer2D import CILViewer2D
import vtk

reader = vtk.vtkMetaImageReader()
reader.SetFileName("C://Users/ofn77899/Documents/GitHub/CCPi-Simpleflex/data/head.mha")
reader.Update()

v = CILViewer2D()

v.setInput3DData(reader.GetOutput())
v.displaySlice(42)
#v.iren.Start()

print (v.getROI())