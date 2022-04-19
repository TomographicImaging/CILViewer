from ccpi.viewer import viewer2D
import vtk

v = viewer2D()
reader = vtk.vtkMetaImageReader()
reader.SetFileName("head.mha")
reader.Update()
v.setInputData(reader.GetOutput())
v.startRenderLoop()
