import numpy as np
import vtk
import os
from ccpi.viewer import viewer2D
from ccpi.viewer.utils.conversion import Converter
from tqdm import tqdm

def WriteMETAImageHeader(data_filename, header_filename, typecode, big_endian, header_length, shape, spacing=(1.,1.,1.), origin=(0.,0.,0.)):
    '''Writes a NumPy array and a METAImage text header so that the npy file can be used as data file
    
    :param filename: name of the single file containing the data
    :param typecode:
    '''
    

    # inspired by
    # https://github.com/vejmarie/vtk-7/blob/master/Wrapping/Python/vtk/util/vtkImageImportFromArray.py
    # and metaTypes.h in VTK source code
    __typeDict = {'b':'MET_CHAR',    # VTK_SIGNED_CHAR,     # int8
                  'B':'MET_UCHAR',   # VTK_UNSIGNED_CHAR,   # uint8
                  'h':'MET_SHORT',   # VTK_SHORT,           # int16
                  'H':'MET_USHORT',  # VTK_UNSIGNED_SHORT,  # uint16
                  'i':'MET_INT',     # VTK_INT,             # int32
                  'I':'MET_UINT',    # VTK_UNSIGNED_INT,    # uint32
                  'f':'MET_FLOAT',   # VTK_FLOAT,           # float32
                  'd':'MET_DOUBLE',  # VTK_DOUBLE,          # float64
                  'F':'MET_FLOAT',   # VTK_FLOAT,           # float32
                  'D':'MET_DOUBLE'   # VTK_DOUBLE,          # float64
          }

    # typecode = array.dtype.char
    # print ("typecode,",typecode)
    ar_type = __typeDict[typecode]
    # save header
    # minimal header structure
    # NDims = 3
    # DimSize = 181 217 181
    # ElementType = MET_UCHAR
    # ElementSpacing = 1.0 1.0 1.0
    # ElementByteOrderMSB = False
    # ElementDataFile = brainweb1.raw
    header = 'ObjectType = Image\n'
    header = ''
    header += 'NDims = {0}\n'.format(len(shape))
    header += 'DimSize = {} {} {}\n'.format(shape[0], shape[1], shape[2])
    header += 'ElementType = {}\n'.format(ar_type)
    header += 'ElementSpacing = {} {} {}\n'.format(spacing[0], spacing[1], spacing[2])
    header += 'Position = {} {} {}\n'.format(origin[0], origin[1], origin[2])
    # MSB (aka big-endian)
    # MSB = 'True' if descr['descr'][0] == '>' else 'False'
    header += 'ElementByteOrderMSB = {}\n'.format(big_endian)

    header += 'HeaderSize = {}\n'.format(header_length)
    header += 'ElementDataFile = {}'.format(os.path.abspath(data_filename))

    with open(header_filename , 'w') as hdr:
        hdr.write(header)


def parseNpyHeader(filename):
    '''parses a npy file and returns a dictionary with version, header length and description

    See https://www.numpy.org/devdocs/reference/generated/numpy.lib.format.html for details
    of information included in the output.
    '''
    import struct
    with open(filename, 'rb') as f:
        c = f.read(6)
        if not c == b"\x93NUMPY":
            raise TypeError('File Type is not npy')
        major = struct.unpack('@b', f.read(1))[0]
        minor = struct.unpack('@b', f.read(1))[0]
        if major == 1:
            HEADER_LEN_SIZE = 2
        elif major == 2:
            HEADER_LEN_SIZE = 4

        # print ('NumPy file version {}.{}'.format(major, minor))
        HEADER_LEN = struct.unpack('<H', f.read(HEADER_LEN_SIZE))[0]
        # print ("header_len", HEADER_LEN, type(HEADER_LEN))
        descr = ''
        i = 0
    with open(filename, 'rb') as f:
        f.seek(6+2 + HEADER_LEN_SIZE)

        while i < HEADER_LEN:
            c = f.read(1)
            c = c.decode("utf-8")
            #print (c)
            descr += c
            i += 1
    return {'type': 'NUMPY',
            'version_major':major,
            'version_minor':minor,
            'header_length':HEADER_LEN + 6 + 2 + HEADER_LEN_SIZE,
            'description'  : eval(descr)}

type_to_bytes = {'b':1,    # VTK_SIGNED_CHAR,     # int8
                  'B':1,   # VTK_UNSIGNED_CHAR,   # uint8
                  'h':2,   # VTK_SHORT,           # int16
                  'H':2,  # VTK_UNSIGNED_SHORT,  # uint16
                  'i':4,     # VTK_INT,             # int32
                  'I':4,    # VTK_UNSIGNED_INT,    # uint32
                  'f':4,   # VTK_FLOAT,           # float32
                  'd':8,  # VTK_DOUBLE,          # float64
                  'F':4,   # VTK_FLOAT,           # float32
                  'D':8   # VTK_DOUBLE,          # float64
          }

if __name__ == "__main__":
    fname = os.path.abspath(r"D:\Documents\Dataset\CCPi\DVC\f000_crop\frame_000_f.npy")
    # fname = os.path.abspath('contiguous.npy')
    descr = parseNpyHeader(fname)
    print (descr['description']['descr'][1:])

    # find the typecode of the data and the number of bytes per pixel
    typecode = ''
    nbytes = 0
    for t in [np.uint8, np.int8, np.int16, np.uint16, np.int32, np.uint32, np.float16, np.float32, np.float64]:
        array_descr = descr['description']['descr'][1:]
        if array_descr == np.dtype(t).descr[0][1][1:]:
            typecode = np.dtype(t).char
            nbytes = type_to_bytes[typecode]
            print ("Array TYPE: ", t, array_descr, typecode)            
            break
    
    print ("typecode", typecode)
    print (descr)



    # read in 50 slices
    # start_slice = 1255 
    # end_slice = 1260
    readshape = descr['description']['shape']
    is_fortran = descr['description']['fortran_order']
    
    if is_fortran:
        shape = list(readshape)
        
    else:
        shape = list(readshape)[::-1]
        

    total_size = shape[0] * shape[1] * shape[2]
    axis_size = 512
    max_size = axis_size**3
    axis_magnification = np.power(max_size/total_size, 1/3)
    reduction_factor = np.int(1/axis_magnification)

    # we will read in 5 slices at a time
    low_slice = []
    for i in range (0,shape[2], reduction_factor):
        low_slice.append(
             i
            )

    low_slice.append(shape[2] )
    print (low_slice)
    print (len(low_slice))

    z_axis_magnification = (len(low_slice)-1)/shape[2]
    print ("z_axis_magnification", z_axis_magnification)
    print ("xy_axis magnification", axis_magnification, int(axis_magnification * shape[0]), int(axis_magnification * shape[1]))
    
    target_image_shape = (int(axis_magnification * shape[0]), 
                          int(axis_magnification * shape[1]), 
                          len(low_slice) -1)
    print (target_image_shape)
    
    resampler = vtk.vtkImageReslice()
    resampler.SetOutputExtent(0,target_image_shape[0],
                              0,target_image_shape[1],
                              0,0)
    resampler.SetOutputSpacing(1/axis_magnification, 1/axis_magnification, 1/z_axis_magnification)
    
    # resampler = vtk.vtkImageResample()
    # resampler.SetAxisMagnificationFactor(0, axis_magnification)
    # resampler.SetAxisMagnificationFactor(1, axis_magnification)
    # resampler.SetAxisMagnificationFactor(2, z_axis_magnification)


    print ("allocate vtkImageData")
    resampled_image = vtk.vtkImageData()
    resampled_image.SetExtent(0,target_image_shape[0],
                              0,target_image_shape[1],
                              0,target_image_shape[2])
    resampled_image.SetSpacing(1/axis_magnification, 1/axis_magnification, 1/z_axis_magnification)
    resampled_image.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)

    # in bytes
    slice_length = shape[1] * shape[0] * nbytes


    

    
    big_endian = 'True' if descr['description']['descr'][0] == '>' else 'False'
    #dimensions = descr['description']['shape']
    header_filename = "header.mhd"
    
    


    # print ("whole file ", ndarray.flags)
    # ndarray = np.load(fname, mmap_mode="r")

    

    
    # print ("load whole dataset")
    # ndarray = np.load(fname, mmap_mode="r")
    # print ("save as contiguous")
    # np.save('contiguous.npy', np.ascontiguousarray(ndarray))
    # print ("Done")
    
    # # nvtk = Converter.numpy2vtkImage(np.asarray(ndarray[start_slice:end_slice]), deep=1)
    
    # # print ("VTK: ", nvtk.GetDimensions())
    # # v.setInputData(nvtk)

    # # ndarray = np.load(fname)
    # # v.setInputAsNumpy(ndarray)

    
    #resampler.Update()
    reader = vtk.vtkMetaImageReader()
    resampler.SetInputData(reader.GetOutput())
    # resampler.SetInputConnection(reader.GetOutputPort())
        
           
    npresampled = Converter.vtk2numpy(resampled_image)

    for i,el in tqdm(enumerate(low_slice)):
        end_slice = el
        start_slice = end_slice - reduction_factor
        # print (i, start_slice, end_slice)
        header_length = descr['header_length'] + el * slice_length
        shape[2] = end_slice - start_slice
        WriteMETAImageHeader(fname, 
                             header_filename, 
                             typecode, 
                             big_endian, 
                             header_length, 
                             tuple(shape), 
                             spacing=(1.,1.,1.), 
                             origin=(0.,0.,0.))
        reader.SetFileName(header_filename)
        # reader.Update()

        reader.SetFileName('pippo')
        reader.SetFileName(header_filename)
        reader.Update()

        extent = (0,target_image_shape[0], 
                  0,target_image_shape[1],
                  i,i)
        resampler.SetOutputExtent(extent)
        resampler.Update()
        
        # numpy way
        # res_output = Converter.vtk2numpy(resampler.GetOutput())
        # npresampled[i] = res_output[:]
        # vtk way
        resampled_image.CopyAndCastFrom( resampler.GetOutput(), extent )

    # big image is
    # not_resampled = np.load(fname)
    # vtk_not_resampled = Converter.numpy2vtkImage(not_resampled)
    
    v = viewer2D()
    v.setInputData(resampled_image)
    # v.setInputData2(vtk_not_resampled)

    # lut = v.lut2
    # lut.SetNumberOfColors(16)
    # lut.SetHueRange(.2,.8)
    # lut.SetSaturationRange(.1, .6)
    # lut.SetValueRange(100, 200)
    # lut.SetAlphaRange(0,0.5)
    # lut.Build()
    # v.sliceActor2.Update()

    v.sliceActor.SetInterpolate(True)

    print("interpolated?" , v.sliceActor.GetInterpolate())
    v.startRenderLoop()

