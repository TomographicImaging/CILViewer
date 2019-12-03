from ccpi.viewer import *
import vtk

reader = vtk.vtkMetaImageReader()
reader.SetFileName('head.mha')
reader.Update()

v = viewer3D()
v.setInputData(reader.GetOutput())
v.startRenderLoop()

v.setVolumeColorLevelWindow(2000,2500)
v.startRenderLoop()

v.volume.VisibilityOff()

v.startRenderLoop()