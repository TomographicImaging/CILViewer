# -*- coding: utf-8 -*-
#   Copyright 2017 Edoardo Pasca
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
Created on Thu Jul 27 12:18:58 2017

@author: ofn77899
"""

#!/usr/bin/env python
 
import sys
import vtk
from PyQt5 import QtCore, QtWidgets
from ccpi.viewer.QVTKCILViewer import QVTKCILViewer
from ccpi.viewer.CILViewer2D import CILViewer2D , Converter, CILInteractorStyle
import numpy
 
class CILWidget(QtWidgets.QMainWindow):
 
    def __init__(self, parent = None):
        QtWidgets.QMainWindow.__init__(self, parent)
 
        self.frame = QtWidgets.QFrame()
 
        self.vl = QtWidgets.QVBoxLayout()
        self.vtkWidget = QVTKCILViewer(self.frame)
        self.iren = self.vtkWidget.GetInteractor()
        self.vl.addWidget(self.vtkWidget)
        
        
   
        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)
        

    def displayExample(self):
        # Create source
        source = vtk.vtkSphereSource()
        source.SetCenter(0, 0, 0)
        source.SetRadius(5.0)
   
        # Create a mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())
 
        # Create an actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        self.ren = self.vtkWidget.GetRenderer()
        
        self.ren.AddActor(actor)
        self.show()
        self.iren.Initialize()

    def display(self, imageData):
        print ("and here")
        if type(imageData) == vtk.vtkCommonDataModelPython.vtkImageData:
            self.vtkWidget.setInput3DData(imageData)
        elif type(imageData) == numpy.ndarray:
            self.vtkWidget.setInputAsNumpy(imageData)
        self.iren.Initialize()
        print ("down here")
        try:
            self.show()
        except Error:
            print ("error")


import threading
class viewer(threading.Thread):

    def __init__(self, **kwargs):
        self.window = CILWidget()
        #app = QtWidgets.QApplication(['MainWindow'])
 
        #super(viewer, self).__init__(kwargs)
        
    def display(self, img):
        print("come here")
        self.window.display(img)


        
def runme(): 
    #app = QtWidgets.QApplication(sys.argv)
    app = QtWidgets.QApplication(['MainWindow'])
 
    window = CILWidget()
##    reader = vtk.vtkMetaImageReader()
##    reader.SetFileName("C:\\Users\\ofn77899\\Documents\\GitHub\\CCPi-Simpleflex\\data\\head.mha")
##    reader.Update()
    
##    window.display(reader.GetOutput())
 
    X = numpy.load("C:\\Users\\ofn77899\\Documents\\GitHub\\CCPi-FISTA_reconstruction\\src\\Python\\test\\FISTA.npy")
    window.display(X)  
    sys.exit(app.exec_())


if __name__ == "__main__":
    #   runme()
    X = numpy.load("C:\\Users\\ofn77899\\Documents\\GitHub\\CCPi-FISTA_reconstruction\\src\\Python\\test\\FISTA.npy")
    print ("hello World")
