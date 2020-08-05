# -*- coding: utf-8 -*-
#   Copyright 2019 Edoardo Pasca
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
CILViewer utils

Created on Wed Jan 16 14:21:00 2019

@author: Edoardo Pasca
"""
import os
from numbers import Integral, Number
import math
import numpy
import vtk
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtk.util import numpy_support , vtkImageImportFromArray

import functools
import tempfile
import numpy as np


# Converter class
class Converter(object):
    # inspired by
    # https://github.com/vejmarie/vtk-7/blob/master/Wrapping/Python/vtk/util/vtkImageImportFromArray.py
    # and metaTypes.h in VTK source code
    numpy_dtype_char_to_MetaImageType = {'b':'MET_CHAR',    # VTK_SIGNED_CHAR,     # int8
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
    numpy_dtype_char_to_bytes = {'b':1,    # VTK_SIGNED_CHAR,     # int8
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
    numpy_dtype_char_to_vtkType = {'b': vtk.VTK_SIGNED_CHAR,     # int8
                                   'B': vtk.VTK_UNSIGNED_CHAR,   # uint8
                                   'h': vtk.VTK_SHORT,           # int16
                                   'H': vtk.VTK_UNSIGNED_SHORT,  # uint16
                                   'i': vtk.VTK_INT,             # int32
                                   'I': vtk.VTK_UNSIGNED_INT,    # uint32
                                   'f': vtk.VTK_FLOAT,           # float32
                                   'd': vtk.VTK_DOUBLE,          # float64
                                   'F': vtk.VTK_FLOAT,           # float32
                                   'D': vtk.VTK_DOUBLE           # float64
    }
    MetaImageType_to_vtkType = {'MET_CHAR': vtk.VTK_SIGNED_CHAR,     # int8
                                'MET_UCHAR': vtk.VTK_UNSIGNED_CHAR,   # uint8
                                'MET_SHORT': vtk.VTK_SHORT,           # int16
                                'MET_USHORT': vtk.VTK_UNSIGNED_SHORT,  # uint16
                                'MET_INT': vtk.VTK_INT,             # int32
                                'MET_UINT': vtk.VTK_UNSIGNED_INT,    # uint32
                                'MET_FLOAT': vtk.VTK_FLOAT,           # float32
                                'MET_DOUBLE': vtk.VTK_DOUBLE,          # float64
                                'MET_FLOAT': vtk.VTK_FLOAT,           # float32
                                'MET_DOUBLE': vtk.VTK_DOUBLE,          # float64
    }

    MetaImageType_to_bytes= {'MET_CHAR': 1,    # VTK_SIGNED_CHAR,     # int8
                             'MET_UCHAR': 1,   # VTK_UNSIGNED_CHAR,   # uint8
                                 'MET_SHORT':2,   # VTK_SHORT,           # int16
                                 'MET_USHORT':2,  # VTK_UNSIGNED_SHORT,  # uint16
                                 'MET_INT':4,     # VTK_INT,             # int32
                                 'MET_UINT':4,    # VTK_UNSIGNED_INT,    # uint32
                                 'MET_FLOAT':4,   # VTK_FLOAT,           # float32
                                 'MET_DOUBLE':8,  # VTK_DOUBLE,          # float64
                                 'MET_FLOAT':4,   # VTK_FLOAT,           # float32
                                 'MET_DOUBLE':8   # VTK_DOUBLE,          # float64
    }
    # Utility functions to transform numpy arrays to vtkImageData and viceversa    
    @staticmethod
    def numpy2vtkImage(nparray, spacing = (1.,1.,1.), origin=(0,0,0), deep=0, output=None):

        shape=numpy.shape(nparray)
        if(nparray.flags["FNC"]):
            order = "F"
            i=0
            k=2
        else:
            order = "C"
            i=2
            k=0

        nparray = nparray.ravel(order)
        vtkarray = numpy_support.numpy_to_vtk(num_array=nparray, deep=deep, array_type=numpy_support.get_vtk_array_type(nparray.dtype))
        vtkarray.SetName('vtkarray')

        if output is None:
            img_data = vtk.vtkImageData()
        else:
            if output.GetNumberOfPoints() > 0:
                raise ValueError('Output variable must be an empty vtkImageData object.')
            else:
                img_data = output

        img_data.GetPointData().AddArray(vtkarray)
        img_data.SetExtent(0,shape[i]-1,0,shape[1]-1,0,shape[k]-1)
        img_data.GetPointData().SetActiveScalars('vtkarray')
        img_data.SetOrigin(origin)
        img_data.SetSpacing(spacing)

        return img_data

    @staticmethod
    def vtk2numpy(imgdata, order = None):
        '''Converts the VTK data to 3D numpy array

        Points in a VTK ImageData have indices as X-Y-Z (FORTRAN-contiguos)
        index = x + dimX * y + z * dimX * dimY,
        meaning that the slicing a VTK ImageData is easy in the Z axis

        Points in Numpy have indices as Z-Y-X (C-contiguous)
        index = z + dimZ * y + x * dimZ * dimY
        meaning that the slicing of a numpy array is easy on the X axis

        The function imgdata.GetPointData().GetScalars() returns a pointer to a
        vtk<TYPE>Array where the data is stored as X-Y-Z.
        '''
        img_data = numpy_support.vtk_to_numpy(
                imgdata.GetPointData().GetScalars())

        dims = imgdata.GetDimensions()
        # print ("vtk2numpy: VTKImageData dims {0}".format(dims))

        # print("chosen order ", order)

        img_data.shape = (dims[2],dims[1],dims[0])

        if(order == 'F'):
            img_data = numpy.transpose(img_data, [2,1,0])
            img_data = numpy.asfortranarray(img_data)

        return img_data


# TODO:  Get rid of the below and make a tiff to vtk method and a tiff resample reader.
    @staticmethod
    def vtkTiffStack2numpy(filenames):
        '''Reads the TIFF stack with VTK. 
        
        This implementation should supersede all the others
        '''
        reader = vtk.vtkTIFFReader()
        sa = vtk.vtkStringArray()
        for fname in filenames:
            # should check if file is accessible etc
            sa.InsertNextValue(fname)

        reader.SetFileNames(sa)
        reader.Update()
        return Converter.vtk2numpy(reader.GetOutput())
        
    @staticmethod
    def tiffStack2numpy(filename=None, indices=None, extent = None,
                        sampleRate = None, flatField = None, darkField = None,
                        filenames= None, tiffOrientation=1):
        '''Converts a stack of TIFF files to numpy array.
        
        filename must contain the whole path. The filename is supposed to be named and
        have a suffix with the ordinal file number, i.e. /path/to/projection_%03d.tif
        
        indices are the suffix, generally an increasing number
        
        Optionally extracts only a selection of the 2D images and (optionally)
        normalizes.
        '''
        
        if filename is not None and indices is not None:
            filenames = [ filename % num for num in indices]
        return Converter._tiffStack2numpy(filenames=filenames, extent=extent,
                                         sampleRate=sampleRate,
                                         flatField=flatField,
                                         darkField=darkField)
    @staticmethod
    def tiffStack2numpyEnforceBounds(filename=None, indices=None,
                        extent = None , sampleRate = None ,
                        flatField = None, darkField = None
                        , filenames= None, tiffOrientation=1, bounds=(512,512,512)):
        """
        Converts a stack of TIFF files to numpy array. This is constrained to a 512x512x512 cube

        filename must contain the whole path. The filename is supposed to be named and
        have a suffix with the ordinal file number, i.e. /path/to/projection_%03d.tif

        indices are the suffix, generally an increasing number

        Optionally extracts only a selection of the 2D images and (optionally)
        normalizes.

        :param (string) filename:   full path prefix
        :param (list)   indices:    Indices to append to path for file selection
        :param (tuple)  extent:     Allows option to select a subset
        :param (tuple)  sampleRate: Allows downsampling to reduce data load on visualiser
        :param          flatField:  --
        :param          darkField:  --
        :param (list)   filenames:  Filenames for processing
        :param (int)    tiffOrientation: --
        :param (tuple)  bounds:     Maximum size of display cube (x,y,z)

        :return (numpy.ndarray): Image data as a numpy array
        """

        if filename is not None and indices is not None:
            filenames = [filename % num for num in indices]

        # Get number of files as an index value
        file_index = len(filenames) - 1

        # Get the xy extent of the first image in the list
        if extent is None:
            reader = vtk.vtkTIFFReader()
            reader.SetFileName(filenames[0])
            reader.SetOrientationType(tiffOrientation)
            reader.Update()
            img_ext = reader.GetOutput().GetExtent()

            stack_extent =  img_ext[0:5] + (file_index,)
            size = stack_extent[1::2]
        else:
            size = extent[1::2]

        # Calculate re-sample rate
        sample_rate = tuple(map(lambda x,y: math.ceil(float(x)/y), size, bounds))

        # If a user has defined resample rate, check to see which has higher factor and keep that
        if sampleRate is not None:
            sampleRate = Converter.highest_tuple_element(sampleRate, sample_rate)
        else:
            sampleRate = sample_rate

        # Re-sample input filelist
        list_sample_index = sampleRate[2]
        filenames = filenames[::list_sample_index]

        return Converter._tiffStack2numpy(filenames=filenames, extent=extent,
                                          sampleRate=sampleRate,
                                          flatField=flatField,
                                          darkField=darkField)

    @staticmethod
    def _tiffStack2numpy(filenames,
                        extent = None , sampleRate = None ,\
                        flatField = None, darkField = None, tiffOrientation=1):
        '''Converts a stack of TIFF files to numpy array.
        
        filename must contain the whole path. The filename is supposed to be named and
        have a suffix with the ordinal file number, i.e. /path/to/projection_%03d.tif
        
        indices are the suffix, generally an increasing number
        
        Optionally extracts only a selection of the 2D images and (optionally)
        normalizes.
        '''

        stack = vtk.vtkImageData()
        reader = vtk.vtkTIFFReader()
        voi = vtk.vtkExtractVOI()

        stack_image = numpy.asarray([])
        nreduced = len(filenames)

        for num in range(len(filenames)):


            #fn = filename % indices[num]
            fn = filenames[num]
            print ("resampling %s" % ( fn ) )
            reader.SetFileName(fn)
            reader.SetOrientationType(tiffOrientation)
            reader.Update()
            print (reader.GetOutput().GetScalarTypeAsString())
            if num == 0:

                # Extent
                if extent is None:
                    sliced = reader.GetOutput().GetExtent()
                    stack.SetExtent(sliced[0],sliced[1], sliced[2],sliced[3], 0, nreduced-1)

                    if sampleRate is not None:
                        voi.SetSampleRate(sampleRate)
                        ext = numpy.asarray([(sliced[2*i+1] - sliced[2*i])/sampleRate[i] for i in range(3)], dtype=int)
                        stack.SetExtent(0, ext[0], 0, ext[1], 0, nreduced - 1)
                else:
                    sliced = extent
                    voi.SetVOI(extent)

                    # Sample Rate
                    if sampleRate is not None:
                        voi.SetSampleRate(sampleRate)
                        ext = numpy.asarray([(sliced[2*i+1] - sliced[2*i])/sampleRate[i] for i in range(3)], dtype=int)
                        # print ("ext {0}".format(ext))
                        stack.SetExtent(0, ext[0] , 0, ext[1], 0, nreduced-1)
                    else:
                         stack.SetExtent(0, sliced[1] - sliced[0], 0, sliced[3]-sliced[2], 0, nreduced-1)

                # Flatfield
                if (flatField != None and darkField != None):
                    stack.AllocateScalars(vtk.VTK_FLOAT, 1)
                else:
                    stack.AllocateScalars(reader.GetOutput().GetScalarType(), 1)



                print ("Image Size: %d" % ((sliced[1]+1)*(sliced[3]+1) ))
                stack_image = Converter.vtk2numpy(stack)
                print ("Stack shape %s" % str(numpy.shape(stack_image)))

            if extent is not None or sampleRate is not None :
                voi.SetInputData(reader.GetOutput())
                voi.Update()
                img = voi.GetOutput()
            else:
                img = reader.GetOutput()

            theSlice = Converter.vtk2numpy(img)[0]
            if darkField != None and flatField != None:
                print("Try to normalize")
                #if numpy.shape(darkField) == numpy.shape(flatField) and numpy.shape(flatField) == numpy.shape(theSlice):
                theSlice = Converter.normalize(theSlice, darkField, flatField, 0.01)
                print (theSlice.dtype)


            print ("Slice shape %s" % str(numpy.shape(theSlice)))
            stack_image[num] = theSlice.copy()

        return stack_image

    @staticmethod
    def normalize(projection, dark, flat, def_val=0):
        a = (projection - dark)
        b = (flat-dark)
        with numpy.errstate(divide='ignore', invalid='ignore'):
            c = numpy.true_divide( a, b )
            c[ ~ numpy.isfinite( c )] = def_val  # set to not zero if 0/0
        return c

    @staticmethod
    def highest_tuple_element(user,calc):
        """
        Returns a tuple containing the maximum combination in elementwise comparison
        :param (tuple)user:
            User suppliec tuple

        :param (tuple) calc:
            Calculated tuple

        :return (tuple):
            Highest elementwise combination
        """

        output = []
        for u, c in zip(user,calc):
            if u > c:
                output.append(u)
            else:
                output.append(c)

        return tuple(output)



class cilNumpyMETAImageWriter(object):
    '''A Writer to write a Numpy Array in npy format and a METAImage Header

    This way the same data file can be accessed by NumPy and VTK
    '''
    __FileName = None
    __Array = None
    __Spacing = (1.,1.,1.)
    def __init__(self):
        pass

    def SetInputData(self, array):
        if not isinstance (array, numpy.ndarray):
            raise ValueError('Input must be a NumPy array. Got' , type(array))
        self.__Array = array
    def Write(self):
        if self.__Array is None:
            raise ValueError('Array is None')
        if self.__FileName is None:
            raise ValueError('FileName is None')

        WriteNumpyAsMETAImage(self.__Array, self.__FileName, self.__Spacing)
    def SetFileName(self, fname):
        self.__FileName = os.path.abspath(fname)
    def GetFileName(self):
        return self.__FileName
    def SetSpacing(self, value):
        if not (isinstance(value, list) or isinstance(value, tuple)):
            raise ValueError('Spacing should be a list or a tuple. Got', type(value))
        if len(value) != len(self.__Array.shape):
            self.__Spacing = value
            self.Modified()
    @staticmethod
    def  WriteMETAImageHeader(data_filename, header_filename, typecode, big_endian, \
                              header_length, shape, spacing=(1.,1.,1.), origin=(0.,0.,0.)):
        '''Writes a NumPy array and a METAImage text header so that the npy file can be used as data file
        
        :param filename: name of the single file containing the data
        :param typecode: numpy typecode or metaimage type
        '''
        
        if typecode not in ['MET_CHAR',  'MET_UCHAR', 'MET_SHORT', 'MET_USHORT', 'MET_INT', 'MET_UINT', 'MET_FLOAT','MET_DOUBLE','MET_FLOAT','MET_DOUBLE']:
            ar_type = Converter.numpy_dtype_char_to_MetaImageType[typecode]
        else:
            ar_type = typecode

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


    @staticmethod
    def WriteNumpyAsMETAImage(array, filename, spacing=(1.,1.,1.), origin=(0.,0.,0.)):
        '''Writes a NumPy array and a METAImage text header so that the npy file can be used as data file'''
        # save the data as numpy
        datafname = os.path.abspath(filename) + '.npy'
        hdrfname =  os.path.abspath(filename) + '.mhd'
        if (numpy.isfortran(array)):
            numpy.save(datafname, array)
        else:
            numpy.save(datafname, numpy.asfortranarray(array))
        npyhdr = parseNpyHeader(datafname)

        typecode = array.dtype.char
        print ("typecode,",typecode)
        #r_type = Converter.numpy_dtype_char_to_MetaImageType[typecode]
        big_endian = 'True' if npyhdr['description']['descr'][0] == '>' else 'False'
        readshape = descr['description']['shape']
        is_fortran = descr['description']['fortran_order']
        if is_fortran:
            shape = list(readshape)
        else:
            shape = list(readshape)[::-1]
        header_length = npyhdr['header_length']


        cilNumpyMETAImageWriter.WriteMETAImageHeader(datafname, hdrfname, typecode, big_endian, \
                                                     header_length, shape, spacing=spacing, origin=origin)
        # # save header
        # # minimal header structure
        # # NDims = 3
        # # DimSize = 181 217 181
        # # ElementType = MET_UCHAR
        # # ElementSpacing = 1.0 1.0 1.0
        # # ElementByteOrderMSB = False
        # # ElementDataFile = brainweb1.raw
        # header = 'ObjectType = Image\n'
        # header = ''
        # header += 'NDims = {0}\n'.format(len(array.shape))
        # header += 'DimSize = {} {} {}\n'.format(array.shape[0], array.shape[1], array.shape[2])
        # header += 'ElementType = {}\n'.format(ar_type)
        # header += 'ElementSpacing = {} {} {}\n'.format(spacing[0], spacing[1], spacing[2])
        # header += 'Position = {} {} {}\n'.format(origin[0], origin[1], origin[2])
        # # MSB (aka big-endian)
        # descr = npyhdr['description']
        # MSB = 'True' if descr['descr'][0] == '>' else 'False'
        # header += 'ElementByteOrderMSB = {}\n'.format(MSB)

        # header += 'HeaderSize = {}\n'.format(npyhdr['header_length'])
        # header += 'ElementDataFile = {}'.format(os.path.basename(datafname))

        # with open(hdrfname , 'w') as hdr:
        #     hdr.write(header)



def WriteNumpyAsMETAImage(array, filename, spacing=(1.,1.,1.), origin=(0.,0.,0.)):
    '''Writes a NumPy array and a METAImage text header so that the npy file can be used as data file
    
    same as cilNumpyMETAImageWriter.WriteNumpyAsMETAImage'''
    return cilNumpyMETAImageWriter.WriteNumpyAsMETAImage(array, filename, spacing=spacing, origin=origin)

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


class cilBaseResampleReader(VTKPythonAlgorithmBase):
    '''vtkAlgorithm to load and resample a raw file to an approximate memory footprint

    
    '''
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        
        self.__FileName = 1
        self.__TargetShape = (256,256,256)
        self.__IsFortran = False
        self.__BigEndian = False
        self.__FileHeaderLength = 0
        self.__BytesPerElement = 1
        self.__StoredArrayShape = None
        self.__OutputVTKType = None
        self.__NumpyTypeCode = None
        self.__MetaImageTypeCode = None


        
    def SetFileName(self, value):
        '''Sets the value at which the mask is active'''
        if not os.path.exists(value):
            raise ValueError('File does not exist!' , value)

        if value != self.__FileName:
            self.__FileName = value
            self.Modified()

    def GetFileName(self):
        return self.__FileName
    
    def SetTargetShape(self, value):
        if not isinstance (value, tuple):
            raise ValueError('Expected a tuple. Got {}' , type(value))

        if not value == self.__TargetShape:
            self.__TargetShape = value
            self.Modified()
    def GetTargetShape(self):
        return self.__TargetShape

    def FillInputPortInformation(self, port, info):
        '''This is a reader so no input'''
        return 1

    def FillOutputPortInformation(self, port, info):
        '''output should be of vtkImageData type'''
        info.Set(vtk.vtkDataObject.DATA_TYPE_NAME(), "vtkImageData")
        return 1
    
        
    def GetStoredArrayShape(self):
        return self.__StoredArrayShape
    def GetFileHeaderLength(self):
        return self.__FileHeaderLength
    def GetBytesPerElement(self):
        return self.__BytesPerElement
    def GetBigEndian(self):
        return self.__BigEndian
    def GetIsFortran(self):
        return self.__IsFortran
    def GetOutputVTKType(self):
        return self.__OutputVTKType
    def GetNumpyTypeCode(self):
        return self.__NumpyTypeCode
    def GetFileName(self):
        return self.__FileName
    
    def SetStoredArrayShape(self, value):
        if not isinstance (value , tuple):
            raise ValueError('Expected tuple, got {}'.format(type(value)))
        if len(value) != 3:
            raise ValueError('Expected tuple of length 3, got {}'.format(len(value)))
        self.__StoredArrayShape = value
    def SetFileHeaderLength(self, value):
        if not isinstance (value , int):
            raise ValueError('Expected int, got {}'.format(type(value)))
        self.__FileHeaderLength = value
    def SetBytesPerElement(self, value):
        if not isinstance (value , int):
            raise ValueError('Expected int, got {}'.format(type(value)))
        self.__BytesPerElement = value
    def SetBigEndian(self, value):
        if not isinstance (value , bool):
            raise ValueError('Expected bool, got {}'.format(type(value)))
        self.__BigEndian = value
    def SetIsFortran(self, value):
        if not isinstance (value , bool):
            raise ValueError('Expected bool, got {}'.format(type(value)))
        self.__IsFortran = value
    def SetOutputVTKType(self, value):
        if value not in [vtk.VTK_SIGNED_CHAR, vtk.VTK_UNSIGNED_CHAR,  vtk.VTK_SHORT,  vtk.VTK_UNSIGNED_SHORT,\
                         vtk.VTK_INT, vtk.VTK_UNSIGNED_INT,  vtk.VTK_FLOAT, vtk.VTK_DOUBLE, vtk.VTK_FLOAT,  \
                         vtk.VTK_DOUBLE]:
            raise ValueError("Unexpected Type: got {}", value)
        self.__OutputVTKType = value
    def SetNumpyTypeCode(self, value):
        if value not in ['b','B','h','H','i','I','f','d','F','D']:
            raise ValueError("Unexpected Type: got {}", value)
        self.__NumpyTypeCode = value
        self.SetMetaImageTypeCode(Converter.numpy_dtype_char_to_MetaImageType[value])

    def GetMetaImageTypeCode(self):
        return self.__MetaImageTypeCode

    def SetMetaImageTypeCode(self, value):
        
        self.__MetaImageTypeCode = value

    def RequestData(self, request, inInfo, outInfo):
        print("RequestData BaseResampleReader")
        outData = vtk.vtkImageData.GetData(outInfo)

        # get basic info
        nbytes = self.GetBytesPerElement()
        big_endian = self.GetBigEndian()
        readshape = self.GetStoredArrayShape()
        file_header_length = self.GetFileHeaderLength()
        is_fortran = self.GetIsFortran()
        
        if is_fortran:
            shape = list(readshape)
        else:
            shape = list(readshape)[::-1]

        total_size = shape[0] * shape[1] * shape[2]

        # calculate the product of the elements of TargetShape
        max_size = functools.reduce (lambda x,y: x*y, self.GetTargetShape(),1)

        tmpdir = tempfile.mkdtemp()
        header_filename = os.path.join(tmpdir, "header.mhd")
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(header_filename)

        #print("typecode", self.GetNumpyTypeCode())

        if total_size < max_size: #in this case we don't need to resample
            try:
                print("Don't resample")

                cilNumpyMETAImageWriter.WriteMETAImageHeader(self.GetFileName(), 
                                        header_filename, 
                                        self.GetMetaImageTypeCode(),#self.GetNumpyTypeCode(), 
                                        big_endian, 
                                        file_header_length, 
                                        tuple(shape), 
                                        spacing=(1.,1.,1.), #!! Don't we need to set?
                                        origin=(0.,0.,0.)) #??
                reader.Modified()
                reader.Update()
                outData.ShallowCopy(reader.GetOutput())
                print("Finished")

            finally:
                print("Finally")
                os.remove(header_filename)
                os.rmdir(tmpdir)

            return 1

        print("Proceeding")
        # scaling is going to be similar in every axis (xy the same, z possibly different)

        try:
            # scaling is going to be similar in every axis 
            # (xy the same, z possibly different)
            xy_axes_magnification = np.power(max_size/total_size, 1/3)
            slice_per_chunk = np.int(1/xy_axes_magnification)
            
            # indices of the first and last slice per chunk
            # we will read in slice_per_chunk slices at a time
            end_slice_in_chunks = [ i for i in \
                range (slice_per_chunk, shape[2], slice_per_chunk) ]
            # append last slice
            end_slice_in_chunks.append( shape[2] )
            num_chunks = len(end_slice_in_chunks)

            z_axis_magnification = num_chunks / shape[2]
            
            target_image_shape = (int(xy_axes_magnification * shape[0]), 
                                int(xy_axes_magnification * shape[1]), 
                                num_chunks)

            resampler = vtk.vtkImageReslice()
            resampler.SetOutputExtent(0, target_image_shape[0],
                                    0, target_image_shape[1],
                                    0, 0)
            resampler.SetOutputSpacing( 1 / xy_axes_magnification, 
                                        1 / xy_axes_magnification, 
                                        1 / z_axis_magnification)
            # resampled data
            resampled_image = outData
            resampled_image.SetExtent(0, target_image_shape[0],
                                      0, target_image_shape[1],
                                      0, target_image_shape[2])

            resampled_image.SetSpacing(1/xy_axes_magnification,
                                       1/xy_axes_magnification, 
                                       1/z_axis_magnification)
            resampled_image.AllocateScalars(self.GetOutputVTKType(), 1)
        
            # slice size in bytes
            slice_length = shape[1] * shape[0] * nbytes

            #dimensions = descr['description']['shape']
            # tmpdir = tempfile.mkdtemp()
            # header_filename = os.path.join(tmpdir, "header.mhd")

        except Exception as e:
            print(e)

        print("Set the slice length")
        
        try:

            resampler.SetInputData(reader.GetOutput())

            # process each chunk
            for i,el in enumerate(end_slice_in_chunks):
                #print("Inside for")
                end_slice = el
                #print("End slice", el)
                start_slice = end_slice - slice_per_chunk
                #print("Start slice,", start_slice)
                if start_slice < 0:
                    raise ValueError('{} ERROR: Start slice cannot be negative.'\
                        .format(self.__class__.__name__))

                header_length = file_header_length + el * slice_length

                shape[2] = end_slice - start_slice

                #print("Header info: ", [self.GetFileName(), header_filename, self.GetMetaImageTypeCode(),big_endian, header_length, shape])
                cilNumpyMETAImageWriter.WriteMETAImageHeader(
                    self.GetFileName(), 
                    header_filename, 
                    self.GetMetaImageTypeCode(), #self.GetNumpyTypeCode(), 
                    big_endian, 
                    header_length, 
                    tuple(shape), 
                    spacing=(1.,1.,1.), 
                    origin=(0.,0.,0.)
                )
                # force Update
                
                reader.Modified()
                reader.Update()
                # change the extent of the resampled image
                extent = (0,target_image_shape[0], 
                        0,target_image_shape[1],
                        i,i)
                resampler.SetOutputExtent(extent)
                resampler.Update()

                ################# vtk way ####################
                resampled_image.CopyAndCastFrom( resampler.GetOutput(), extent )
                self.UpdateProgress(i/ num_chunks )

        except Exception as e:
            print(e)
        finally:
            os.remove(header_filename)
            os.rmdir(tmpdir)
        
        return 1

    def GetOutput(self):
        return self.GetOutputDataObject(0)

class cilNumpyResampleReader(cilBaseResampleReader):
    '''vtkAlgorithm to load and resample a numpy file to an approximate memory footprint

    
    '''
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilNumpyResampleReader, self).__init__()
        
        self.__FileName = 1
        self.__TargetShape = (256,256,256)
        self.__IsFortran = False
        self.__BigEndian = False
        self.__FileHeaderLength = 0
        self.__BytesPerElement = 1
        self.__StoredArrayShape = None
        self.__OutputVTKType = None
        self.__NumpyTypeCode = None


        
    
    def ReadNpyHeader(self):
        # extract info from the npy header
        descr = parseNpyHeader(self.GetFileName())
        # find the typecode of the data and the number of bytes per pixel
        typecode = ''
        nbytes = 0
        for t in [np.uint8, np.int8, np.int16, np.uint16, np.int32, np.uint32, np.float16, np.float32, np.float64]:
            array_descr = descr['description']['descr'][1:]
            if array_descr == np.dtype(t).descr[0][1][1:]:
                typecode = np.dtype(t).char
                nbytes = Converter.numpy_dtype_char_to_bytes[typecode]
                break
        
        big_endian = 'True' if descr['description']['descr'][0] == '>' else 'False'
        readshape = descr['description']['shape']
        is_fortran = descr['description']['fortran_order']
        file_header_length = descr['header_length']
        
        
        self.__IsFortran = is_fortran
        self.__BigEndian = big_endian
        self.__FileHeaderLength = file_header_length
        self.__BytesPerElement = nbytes
        self.__StoredArrayShape = readshape
        self.__OutputVTKType = Converter.numpy_dtype_char_to_vtkType[typecode]
        self.__MetaImageTypeCode = Converter.numpy_dtype_char_to_MetaImageType[typecode]
        self.SetNumpyTypeCode(typecode)
        
        self.Modified()

        
    def GetStoredArrayShape(self):
        self.ReadNpyHeader()
        return self.__StoredArrayShape
    def GetFileHeaderLength(self):
        self.ReadNpyHeader()
        return self.__FileHeaderLength
    def GetBytesPerElement(self):
        self.ReadNpyHeader()
        return self.__BytesPerElement
    def GetBigEndian(self):
        self.ReadNpyHeader()
        return self.__BigEndian
    def GetIsFortran(self):
        self.ReadNpyHeader()
        return self.__IsFortran
    def GetOutputVTKType(self):
        self.ReadNpyHeader()
        return self.__OutputVTKType
    def GetNumpyTypeCode(self):
        self.ReadNpyHeader()
        return self.__NumpyTypeCode

class cilMetaImageResampleReader(cilBaseResampleReader):
    '''vtkAlgorithm to load and resample a metaimage file to an approximate memory footprint

    
    '''
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilMetaImageResampleReader, self).__init__()
        
        self.__FileName = 1
        self.__TargetShape = (512,512,512)
        self.__IsFortran = False
        self.__BigEndian = False
        self.__FileHeaderLength = 0
        self.__BytesPerElement = 1
        self.__StoredArrayShape = None
        self.__OutputVTKType = None
        self.__MetaImageTypeCode = None
        self.__CompressedData = False
        
    
    def ReadMetaImageHeader(self):
        
        header_length = 0
        with open(self.__FileName, 'rb') as f:
            for line in f:
                header_length += len(line)
                line = str(line, encoding = 'utf-8').strip()
                if 'BinaryDataByteOrderMSB' in line:
                    self.__BigEndian = str(line).split('= ')[-1]
                    print(self.__BigEndian)
                elif 'DimSize'  in line:
                    shape = line.split('= ')[-1].split(' ')[:3]
                    shape[2].strip()
                    for i in range(0,len(shape)):
                        shape[i] = int(shape[i])
                    
                    self.__StoredArrayShape = shape
                    print(self.__StoredArrayShape)
                elif 'ElementType' in line:
                    typecode = line.split('= ')[-1]
                    print(typecode)
                    self.__MetaImageTypeCode = typecode
                elif 'CompressedData' in line:
                    compressed = line.split('= ')[-1]
                    self.__CompressedData = compressed
                    if(self.__CompressedData):
                        print("Cannot resample compressed image")
                        return

                elif 'HeaderSize' in line:
                    header_size = line.split('= ')[-1]
                    self.__FileHeaderLength = int(header_size)

                elif 'ElementDataFile' in line: #signifies end of header
                    element_data_file = line.split('= ')[-1]
                    if element_data_file !='LOCAL': #then we have an mhd file with data in another file
                        file_path = os.path.dirname(self.__FileName)
                        element_data_file = os.path.join(file_path, element_data_file)
                        print("Filename: ", element_data_file)
                        self.__FileName = element_data_file
                    else:
                        self.__FileHeaderLength = header_length
                    break

        print("Continues")

        
        self.__IsFortran = True
        self.__BytesPerElement = Converter.MetaImageType_to_bytes[self.__MetaImageTypeCode]
        self.SetOutputVTKType(Converter.MetaImageType_to_vtkType[self.__MetaImageTypeCode])
        print(self.GetOutputVTKType())
        
        # self.Modified()

        
    def GetStoredArrayShape(self):
        #self.ReadMetaImageHeader()
        return self.__StoredArrayShape
    def GetFileHeaderLength(self):
        #self.ReadMetaImageHeader()
        return self.__FileHeaderLength
    def GetBytesPerElement(self):
        #self.ReadMetaImageHeader()
        return self.__BytesPerElement
    def GetBigEndian(self):
        #self.ReadMetaImageHeader()
        return self.__BigEndian
    def GetIsFortran(self):
        #self.ReadMetaImageHeader()
        return self.__IsFortran

    def SetFileName(self, value):
        print("Setting filename")
        if value != 'LOCAL': #in the case of an mha file, data is stored in the same file.
            if not os.path.exists(value):
                raise ValueError('File does not exist!' , value)

        if value != self.__FileName:
            self.__FileName = value
            print(self.__FileName)
            self.Modified()
            self.ReadMetaImageHeader()
    
    def GetFileName(self):
        return self.__FileName

    def SetMetaImageTypeCode(self, value):
        if value not in ['MET_CHAR',  'MET_UCHAR', 'MET_SHORT', 'MET_USHORT', 'MET_INT', 'MET_UINT', 'MET_FLOAT','MET_DOUBLE','MET_FLOAT','MET_DOUBLE']:
            raise ValueError("Unexpected Type: got {}", value)
        self.__MetaImageTypeCode = value

    def GetMetaImageTypeCode(self):
        return self.__MetaImageTypeCode


class cilBaseCroppedReader(VTKPythonAlgorithmBase):
    '''vtkAlgorithm to crop in  the z direction

    
    '''
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        
        self.__FileName = 1
        self.__IsFortran = False
        self.__BigEndian = False
        self.__FileHeaderLength = 0
        self.__BytesPerElement = 1
        self.__StoredArrayShape = None
        self.__OutputVTKType = None
        self.__NumpyTypeCode = None
        self.__MetaImageTypeCode = None
        self.__TargetZExtent = (0,0)
        self.__Origin = (0,0,0)


        
    def SetFileName(self, value):
        '''Sets the value at which the mask is active'''
        print("Set filename")
        if not os.path.exists(value):
            raise ValueError('File does not exist!' , value)

        if value != self.__FileName:
            self.__FileName = value
            self.Modified()

    def GetFileName(self):
        print("Getting filename")
        return self.__FileName
    

    def FillInputPortInformation(self, port, info):
        '''This is a reader so no input'''
        return 1

    def FillOutputPortInformation(self, port, info):
        '''output should be of vtkImageData type'''
        info.Set(vtk.vtkDataObject.DATA_TYPE_NAME(), "vtkImageData")
        return 1
    
        
    def GetStoredArrayShape(self):
        return self.__StoredArrayShape
    def GetFileHeaderLength(self):
        return self.__FileHeaderLength
    def GetBytesPerElement(self):
        return self.__BytesPerElement
    def GetBigEndian(self):
        return self.__BigEndian
    def GetIsFortran(self):
        return self.__IsFortran
    def GetOutputVTKType(self):
        return self.__OutputVTKType
    def GetNumpyTypeCode(self):
        return self.__NumpyTypeCode
    def GetFileName(self):
        return self.__FileName
    
    def SetStoredArrayShape(self, value):
        if not isinstance (value , tuple):
            raise ValueError('Expected tuple, got {}'.format(type(value)))
        if len(value) != 3:
            raise ValueError('Expected tuple of length 3, got {}'.format(len(value)))
        self.__StoredArrayShape = value
    def SetFileHeaderLength(self, value):
        if not isinstance (value , int):
            raise ValueError('Expected int, got {}'.format(type(value)))
        self.__FileHeaderLength = value
    def SetBytesPerElement(self, value):
        if not isinstance (value , int):
            raise ValueError('Expected int, got {}'.format(type(value)))
        self.__BytesPerElement = value
    def SetBigEndian(self, value):
        if not isinstance (value , bool):
            raise ValueError('Expected bool, got {}'.format(type(value)))
        self.__BigEndian = value
    def SetIsFortran(self, value):
        if not isinstance (value , bool):
            raise ValueError('Expected bool, got {}'.format(type(value)))
        self.__IsFortran = value
    def SetOutputVTKType(self, value):
        if value not in [vtk.VTK_SIGNED_CHAR, vtk.VTK_UNSIGNED_CHAR,  vtk.VTK_SHORT,  vtk.VTK_UNSIGNED_SHORT,\
                         vtk.VTK_INT, vtk.VTK_UNSIGNED_INT,  vtk.VTK_FLOAT, vtk.VTK_DOUBLE, vtk.VTK_FLOAT,  \
                         vtk.VTK_DOUBLE]:
            raise ValueError("Unexpected Type: got {}", value)
        self.__OutputVTKType = value
    def SetNumpyTypeCode(self, value):
        if value not in ['b','B','h','H','i','I','f','d','F','D']:
            raise ValueError("Unexpected Type: got {}", value)
        self.__NumpyTypeCode = value
        self.SetMetaImageTypeCode(Converter.numpy_dtype_char_to_MetaImageType[value])

    def GetMetaImageTypeCode(self):
        return self.__MetaImageTypeCode

    def SetMetaImageTypeCode(self, value):
        
        self.__MetaImageTypeCode = value

    def SetTargetZExtent(self, value):
        if not isinstance (value, tuple):
            raise ValueError('Expected a tuple. Got {}' , type(value))

        if not value == self.__TargetZExtent:
            self.__TargetZExtent = value
            self.Modified()

    
    def GetTargetZExtent(self):
        return self.__TargetZExtent

    def SetOrigin(self, value):
        if not isinstance (value, tuple):
            raise ValueError('Expected a tuple. Got {}' , type(value))

        if not value == self.__Origin:
            self.__Origin = value
            self.Modified()
    
    def GetOrigin(self):
        return self.__Origin

    def RequestData(self, request, inInfo, outInfo):
        outData = vtk.vtkImageData.GetData(outInfo)

        # get basic info
        nbytes = self.GetBytesPerElement()
        big_endian = self.GetBigEndian()
        readshape = self.GetStoredArrayShape()
        file_header_length = self.GetFileHeaderLength()
        is_fortran = self.GetIsFortran()
        
        if is_fortran:
            shape = list(readshape)
        else:
            shape = list(readshape)[::-1]


        tmpdir = tempfile.mkdtemp()
        header_filename = os.path.join(tmpdir, "header.mhd")
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(header_filename)


        if self.GetTargetZExtent()[1] >= shape[2]: #in this case we don't need to resample
            try:
                print("Don't resample")

                cilNumpyMETAImageWriter.WriteMETAImageHeader(self.GetFileName(), 
                                        header_filename, 
                                        self.GetMetaImageTypeCode(),#self.GetNumpyTypeCode(), 
                                        big_endian, 
                                        file_header_length, 
                                        tuple(shape), 
                                        spacing=(1.,1.,1.), #!! Don't we need to set?
                                        origin=(0.,0.,0.)) #??
                reader.Modified()
                reader.Update()
                outData.ShallowCopy(reader.GetOutput())
                print("Finished")

            finally:
                print("Finally")
                os.remove(header_filename)
                os.rmdir(tmpdir)

            return 1
        
        try:
            header_length  = file_header_length + (self.GetTargetZExtent()[0]-1)* shape[1] * shape[0] * nbytes
            shape[2] = self.GetTargetZExtent()[1]- self.GetTargetZExtent()[0] + 1

            cilNumpyMETAImageWriter.WriteMETAImageHeader(self.GetFileName(), 
                                header_filename, 
                                self.GetMetaImageTypeCode(),#self.GetNumpyTypeCode(), 
                                big_endian, 
                                header_length, 
                                tuple(shape), 
                                spacing=(1.,1.,1.), 
                                origin=(0.,0.,0.))
            
            reader.Modified()
            reader.Update()
            # Data = vtk.vtkImageData()
            # print(self.GetStoredArrayShape())
            # print(self.GetTargetZExtent())
            # Data.SetDimensions(self.GetStoredArrayShape())
            # print("Extent", Data.GetExtent())
            # Data.SetSpacing(1,1,1)
            # extent = (0, shape[0], 0, shape[1], self.GetTargetZExtent()[0], self.GetTargetZExtent()[1])
            # print("New extent", Data.GetExtent())
            # print("Inserted extent", extent)
            # Data.CopyAndCastFrom(reader.GetOutput(), extent)
            # outData.ShallowCopy(Data)

            outData.ShallowCopy(reader.GetOutput())
            outData.SetOrigin(self.GetOrigin())
            
            # 

        except Exception as e:
            print(e)
            print("Exception")
        finally:
            os.remove(header_filename)
            os.rmdir(tmpdir)
        return 1

    def GetOutput(self):
        return self.GetOutputDataObject(0)

class cilNumpyCroppedReader(cilBaseCroppedReader):
    '''vtkAlgorithm to load and resample a numpy file to an approximate memory footprint

    
    '''
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilNumpyCroppedReader, self).__init__()
        
        self.__FileName = 1
        self.__TargetShape = (256,256,256)
        self.__IsFortran = False
        self.__BigEndian = False
        self.__FileHeaderLength = 0
        self.__BytesPerElement = 1
        self.__StoredArrayShape = None
        self.__OutputVTKType = None
        self.__NumpyTypeCode = None

        
    
    def ReadNpyHeader(self):
        # extract info from the npy header
        descr = parseNpyHeader(self.GetFileName())
        # find the typecode of the data and the number of bytes per pixel
        typecode = ''
        nbytes = 0
        for t in [np.uint8, np.int8, np.int16, np.uint16, np.int32, np.uint32, np.float16, np.float32, np.float64]:
            array_descr = descr['description']['descr'][1:]
            if array_descr == np.dtype(t).descr[0][1][1:]:
                typecode = np.dtype(t).char
                # nbytes = type_to_bytes[typecode]
                nbytes = Converter.numpy_dtype_char_to_bytes[typecode]
                #print ("Array TYPE: ", t, array_descr, typecode)            
                break

        
        # print ("typecode", typecode)
        # print (descr)
        big_endian = 'True' if descr['description']['descr'][0] == '>' else 'False'
        readshape = descr['description']['shape']
        is_fortran = descr['description']['fortran_order']
        file_header_length = descr['header_length']
        
        
        self.__IsFortran = is_fortran
        self.__BigEndian = big_endian
        self.__FileHeaderLength = file_header_length
        self.__BytesPerElement = nbytes
        self.__StoredArrayShape = readshape
        self.__OutputVTKType = Converter.numpy_dtype_char_to_vtkType[typecode]
        self.__MetaImageTypeCode = Converter.numpy_dtype_char_to_MetaImageType[typecode]
        self.SetNumpyTypeCode(typecode)
        
        self.Modified()

        
    def GetStoredArrayShape(self):
        self.ReadNpyHeader()
        return self.__StoredArrayShape
    def GetFileHeaderLength(self):
        self.ReadNpyHeader()
        return self.__FileHeaderLength
    def GetBytesPerElement(self):
        self.ReadNpyHeader()
        return self.__BytesPerElement
    def GetBigEndian(self):
        self.ReadNpyHeader()
        return self.__BigEndian
    def GetIsFortran(self):
        self.ReadNpyHeader()
        return self.__IsFortran
    def GetOutputVTKType(self):
        self.ReadNpyHeader()
        return self.__OutputVTKType
    def GetNumpyTypeCode(self):
        self.ReadNpyHeader()
        return self.__NumpyTypeCode

class cilMetaImageCroppedReader(cilBaseCroppedReader):
    '''vtkAlgorithm to load and resample a metaimage file to an approximate memory footprint

    
    '''
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilMetaImageCroppedReader, self).__init__()
        
        self.__FileName = 1
        self.__TargetShape = (512,512,512)
        self.__IsFortran = False
        self.__BigEndian = False
        self.__FileHeaderLength = 0
        self.__BytesPerElement = 1
        self.__StoredArrayShape = None
        self.__OutputVTKType = None
        self.__MetaImageTypeCode = None

    
    def ReadMetaImageHeader(self):
        
        header_length = 0
        with open(self.__FileName, 'rb') as f:
                for line in f:
                    header_length += len(line)
                    line = str(line, encoding = 'utf-8').strip()
                    if 'BinaryDataByteOrderMSB' in line:
                        self.__BigEndian = str(line).split('= ')[-1]
                        print(self.__BigEndian)
                    elif 'DimSize'  in line:
                        shape = line.split('= ')[-1].split(' ')[:3]
                        shape[2].strip()
                        for i in range(0,len(shape)):
                            shape[i] = int(shape[i])
                        
                        self.__StoredArrayShape = shape
                        print(self.__StoredArrayShape)
                        print(self.__StoredArrayShape)
                    elif 'ElementType' in line:
                        typecode = line.split('= ')[-1]
                        print(typecode)
                        self.__MetaImageTypeCode = typecode
                    elif 'ElementDataFile' in str(line):
                        break
        self.__FileHeaderLength = header_length
        self.__IsFortran = True
        self.__BytesPerElement = Converter.MetaImageType_to_bytes[self.__MetaImageTypeCode]
        self.SetOutputVTKType(Converter.MetaImageType_to_vtkType[self.__MetaImageTypeCode])
        print(self.GetOutputVTKType())
        
        # self.Modified()

        
    def GetStoredArrayShape(self):
        #self.ReadMetaImageHeader()
        return self.__StoredArrayShape
    def GetFileHeaderLength(self):
        #self.ReadMetaImageHeader()
        return self.__FileHeaderLength
    def GetBytesPerElement(self):
        #self.ReadMetaImageHeader()
        return self.__BytesPerElement
    def GetBigEndian(self):
        #self.ReadMetaImageHeader()
        return self.__BigEndian
    def GetIsFortran(self):
        #self.ReadMetaImageHeader()
        return self.__IsFortran

    def SetFileName(self, value):
        print("Setting filename")
        if value != 'LOCAL': #in the case of an mha file, data is stored in the same file.
            if not os.path.exists(value):
                raise ValueError('File does not exist!' , value)

        if value != self.__FileName:
            self.__FileName = value
            print(self.__FileName)
            self.Modified()
            self.ReadMetaImageHeader()
    
    def GetFileName(self):
        return self.__FileName

    def SetMetaImageTypeCode(self, value):
        if value not in ['MET_CHAR',  'MET_UCHAR', 'MET_SHORT', 'MET_USHORT', 'MET_INT', 'MET_UINT', 'MET_FLOAT','MET_DOUBLE','MET_FLOAT','MET_DOUBLE']:
            raise ValueError("Unexpected Type: got {}", value)
        self.__MetaImageTypeCode = value

    def GetMetaImageTypeCode(self):
        return self.__MetaImageTypeCode

if __name__ == '__main__':
    '''this represent a good base to perform a test for the numpy-metaimage writer'''
    dimX = 128
    dimY = 64
    dimZ = 32
    # a = numpy.zeros((dimX,dimY,dimZ), dtype=numpy.uint16)
    a = numpy.random.randint(0,size=(dimX,dimY,dimZ),high=127,  dtype=numpy.uint16)
    #for x in range(a.shape[0]):
    #    for y in range(a.shape[1]):
    #        for z in range(a.shape[2]):
    #            a[x][y][z] = x + a.shape[0] * y + a.shape[0]*a.shape[1]*z
    for z in range(a.shape[2]):
        b = z * numpy.ones((a.shape[0],a.shape[1]), dtype=numpy.uint8)
        a[:,:,z] = b.copy()

    #arfn = os.path.abspath('C:/Users/ofn77899/Documents/Projects/CCPi/GitHub/CCPi-Simpleflex/data/head.npy')
    arfn = 'test'
    WriteNumpyAsMETAImage(a,arfn)
    hdrdescr = parseNpyHeader(arfn+'.npy')

    #a = numpy.load(arfn+'.npy')

    #import matplotlib.pyplot as plt
    #plt.imshow(a[10,:,:])
    #plt.show()

    reader = vtk.vtkMetaImageReader()
    reader.SetFileName(arfn+'.mhd')
    reader.Update()



    if False:
        from ccpi.viewer.CILViewer2D import CILViewer2D
        v = CILViewer2D()
        v.setInput3DData(reader.GetOutput())
        v.startRenderLoop()
    if False:
        #x = 120
        #y = 60
        #z = 30
        #v1 = a[x][y][z]
        #v2 = numpy.uint8(reader.GetOutput().GetScalarComponentAsFloat(x,y,z,0))
        #print ("value check", v1,v2)
        is_same = a.shape == reader.GetOutput().GetDimensions()

        for z in range(a.shape[2]):
            for y in range(a.shape[1]):
                for x in range(a.shape[0]):
                    v1 = a[x][y][z]
                    v2 = numpy.uint8(reader.GetOutput().GetScalarComponentAsFloat(x,y,z,0))
                    # print ("value check {} {} {},".format((x,y,z) ,v1,v2))
                    is_same = v1 == v2
                    if not is_same:
                        raise ValueError('arrays do not match', v1,v2,x,y,z)
        print ('YEEE array match!')


