import numpy as np
import os
import matplotlib.pyplot as plt
import sys
import functools
import vtk
#https://numpy.org/devdocs/reference/arrays.dtypes.html
# notice that vtk 8.1.2 cannot read very large raw files as the offset is unsigned long
# https://github.com/Kitware/VTK/blob/c3b3b592c7c7e9a1fd34978a41a119cc681b75d5/IO/Image/vtkImageReader.cxx#L141
# this is not the case in vtk 9
from ccpi.viewer.utils import Converter

fname = os.path.abspath("C:/Users/ofn77899/Data/dvc/catherine/104506_distortion_corrected_2560_2560_1600_16bit.raw")
is_fortran = True
shape = (2560, 2560, 1600)
if is_fortran:
    shape = shape[::-1]
is_big_endian = True # little endian
typecode = '5' if len(sys.argv) == 1 else sys.argv[1] # this in the interface is 0, 1, 2, 3, for int8, uint8, int16, uint16
dt_txt = ""
if is_big_endian:
    dt_txt = ">" # big endian
else:
    dt_txt = "<"

slice_size = shape[1]*shape[2]
slice_idx = shape[0]//2
slice_idx = 0 if len(sys.argv) == 2 else int(sys.argv[2])
offset = slice_idx * slice_size
expected_size = functools.reduce(lambda x,y: x*y, shape)
bytes_per_element = 1

if typecode == '0':
    dt_txt += "i1"
elif typecode == '1':
    dt_txt += "u1"
elif typecode == '2':
    dt_txt += "i2"
    bytes_per_element = 2
elif typecode == '3':
    dt_txt += "u2"
    bytes_per_element = 2
elif typecode == '4':
    dt_txt += "i4"
    bytes_per_element = 4
elif typecode == '5':
    dt_txt += "u4"
    bytes_per_element = 4

offset = offset * bytes_per_element
expected_size *= bytes_per_element

print("expected size: ", expected_size)
print("measured size: ", os.stat(fname).st_size)
print("failed: ", 2271734784)

dtype = np.dtype(dt_txt)
# read one slice


data = np.fromfile(fname, dtype=dtype, offset=offset, count=slice_size).reshape(shape[1:])


plt.imshow(data, cmap='gray', origin='lower')
plt.colorbar()
plt.show()


#### VTK doesn't seem to be able to handle very large files as the offset is (unsigned) long
#### https://github.com/Kitware/VTK/blob/f2c452c9c42005672a3f3ed9218dd9a7fecca79a/IO/Image/vtkImageReader.cxx#L162
#### So the only way to read a very large file is to read it in chunks, saving the chunk to a temporary file
#### and then read the temporary file with vtkImageReader2


# err = vtk.vtkFileOutputWindow()
# err.SetFileName("viewer.log")
# vtk.vtkOutputWindow.SetInstance(err)

reader = vtk.vtkImageReader()
reader.SetFileName(fname)
reader.SetDataScalarTypeToUnsignedShort()
if is_big_endian:
    reader.SetDataByteOrderToBigEndian()
else:
    reader.SetDataByteOrderToLittleEndian()

reader.SetFileDimensionality(len(shape))
vtkshape = shape[:]
if is_fortran:
    vtkshape = shape[::-1]
# vtkshape = shape[:]
reader.SetDataExtent(0, vtkshape[0]-1, 0, vtkshape[1]-1, 0, vtkshape[2]-1)
reader.SetDataSpacing(1, 1, 1)
reader.SetDataOrigin(0, 0, 0)

reader.SetDataVOI(0,vtkshape[0]-1, 
                  0,vtkshape[1]-1, 
                #   vtkshape[2]//2,vtkshape[2]//2)
                slice_idx, slice_idx)
print("reading")
reader.Update()
print("reading done")
from ccpi.viewer import CILViewer2D as viewer2D



v = viewer2D.CILViewer2D()
v.setInputData(reader.GetOutput())
v.startRenderLoop()

with open(fname, 'br') as f:
    f.seek(offset)
    raw_data = f.read(slice_size*bytes_per_element)
    with open("test.raw", 'wb') as f2:
        f2.write(raw_data)

reader2 = vtk.vtkImageReader2()
reader2.SetFileName("test.raw")

vtktype = Converter.dtype_name_to_vtkType[dtype.name]
reader2.SetDataScalarType(vtktype)

if is_big_endian:
    reader2.SetDataByteOrderToBigEndian()
else:
    reader2.SetDataByteOrderToLittleEndian()

reader2.SetFileDimensionality(len(shape))
vtkshape = shape[:]
if is_fortran:
    vtkshape = shape[::-1]
# vtkshape = shape[:]
reader2.SetDataExtent(0, vtkshape[0]-1, 0, vtkshape[1]-1, slice_idx, slice_idx)
reader2.SetDataSpacing(1, 1, 1)
reader2.SetDataOrigin(0, 0, 0)

print("reading")
reader2.Update()
print("reading done")

v.setInputData(reader2.GetOutput())
v.startRenderLoop()

del v, reader2
os.remove("test.raw")