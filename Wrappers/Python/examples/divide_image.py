import vtk

reader = vtk.vtkMetaImageReader()
reader.SetFileName("head.mha")
reader.Update()
transform = vtk.vtkTransform()
extent = reader.GetOutput().GetExtent()
centre = [extent[1]/2, extent[3]/2, extent[5]/2]

transform.Translate(centre)
transform.RotateWXYZ(45, 0,0,1)
transform.Translate([-el for el in centre])

math = vtk.vtkImageReslice()
math.SetResliceTransform(transform)
math.SetInputConnection(reader.GetOutputPort())
math.SetOutputSpacing(reader.GetOutput().GetSpacing())
math.SetOutputOrigin(reader.GetOutput().GetOrigin())
math.SetOutputExtent(reader.GetOutput().GetExtent())
math.Update()

writer = vtk.vtkMetaImageWriter()
writer.SetFileName("head_root.mha")
writer.SetInputConnection(math.GetOutputPort())
writer.Write()