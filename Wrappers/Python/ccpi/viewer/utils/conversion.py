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
import math
import numpy
import vtk
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtk.util import numpy_support

import tempfile
import numpy as np
from ccpi.viewer.utils.hdf5_io import HDF5Reader, HDF5SubsetReader

import shutil


# Converter class
class Converter(object):
    # inspired by
    # https://github.com/vejmarie/vtk-7/blob/master/Wrapping/Python/vtk/util/vtkImageImportFromArray.py
    # and metaTypes.h in VTK source code
    numpy_dtype_char_to_MetaImageType = {
        'b': 'MET_CHAR',    # VTK_SIGNED_CHAR,     # int8
        'B': 'MET_UCHAR',   # VTK_UNSIGNED_CHAR,   # uint8
        'h': 'MET_SHORT',   # VTK_SHORT,           # int16
        'H': 'MET_USHORT',  # VTK_UNSIGNED_SHORT,  # uint16
        'i': 'MET_INT',     # VTK_INT,             # int32
        'l': 'MET_INT',     # VTK_INT,             # int32
        'I': 'MET_UINT',    # VTK_UNSIGNED_INT,    # uint32
        'L': 'MET_UINT',    # VTK_UNSIGNED_INT,    # uint32
        'f': 'MET_FLOAT',   # VTK_FLOAT,           # float32
        'd': 'MET_DOUBLE',  # VTK_DOUBLE,          # float64
        'F': 'MET_FLOAT',   # VTK_FLOAT,           # float32
        'D': 'MET_DOUBLE'   # VTK_DOUBLE,          # float64
    }
    numpy_dtype_char_to_bytes = {
        'b': 1,    # VTK_SIGNED_CHAR,     # int8
        'B': 1,   # VTK_UNSIGNED_CHAR,   # uint8
        'h': 2,   # VTK_SHORT,           # int16
        'H': 2,  # VTK_UNSIGNED_SHORT,  # uint16
        'i': 4,     # VTK_INT,             # int32
        'l': 4,     # VTK_INT,             # int32
        'I': 4,    # VTK_UNSIGNED_INT,    # uint32
        'L': 4,    # VTK_UNSIGNED_INT,    # uint32
        'f': 4,   # VTK_FLOAT,           # float32
        'd': 8,  # VTK_DOUBLE,          # float64
        'F': 4,   # VTK_FLOAT,           # float32
        'D': 8   # VTK_DOUBLE,          # float64
    }
    numpy_dtype_char_to_vtkType = {
        'b': vtk.VTK_SIGNED_CHAR,     # int8
        'B': vtk.VTK_UNSIGNED_CHAR,   # uint8
        'h': vtk.VTK_SHORT,           # int16
        'H': vtk.VTK_UNSIGNED_SHORT,  # uint16
        'i': vtk.VTK_INT,             # int32
        'I': vtk.VTK_UNSIGNED_INT,    # uint32
        'L': vtk.VTK_UNSIGNED_INT,    # uint32
        'f': vtk.VTK_FLOAT,           # float32
        'd': vtk.VTK_DOUBLE,          # float64
        'F': vtk.VTK_FLOAT,           # float32
        'D': vtk.VTK_DOUBLE           # float64
    }
    MetaImageType_to_vtkType = {
        'MET_CHAR': vtk.VTK_SIGNED_CHAR,     # int8
        'MET_UCHAR': vtk.VTK_UNSIGNED_CHAR,   # uint8
        'MET_SHORT': vtk.VTK_SHORT,           # int16
        'MET_USHORT': vtk.VTK_UNSIGNED_SHORT,  # uint16
        'MET_INT': vtk.VTK_INT,             # int32
        'MET_UINT': vtk.VTK_UNSIGNED_INT,    # uint32
        'MET_FLOAT': vtk.VTK_FLOAT,           # float32
        'MET_DOUBLE': vtk.VTK_DOUBLE,          # float64
    }

    MetaImageType_to_bytes = {
        'MET_CHAR': 1,    # VTK_SIGNED_CHAR,     # int8
        'MET_UCHAR': 1,   # VTK_UNSIGNED_CHAR,   # uint8
        'MET_SHORT': 2,   # VTK_SHORT,           # int16
        'MET_USHORT': 2,  # VTK_UNSIGNED_SHORT,  # uint16
        'MET_INT': 4,     # VTK_INT,             # int32
        'MET_UINT': 4,    # VTK_UNSIGNED_INT,    # uint32
        'MET_FLOAT': 4,   # VTK_FLOAT,           # float32
        'MET_DOUBLE': 8,  # VTK_DOUBLE,          # float64
    }

    raw_dtype_char_to_MetaImageType = {
        'int8': 'MET_CHAR',    # VTK_SIGNED_CHAR,     # int8
        'uint8': 'MET_UCHAR',   # VTK_UNSIGNED_CHAR,   # uint8
        'int16': 'MET_SHORT',   # VTK_SHORT,           # int16
        'uint16': 'MET_USHORT',  # VTK_UNSIGNED_SHORT,  # uint16
        'int32': 'MET_INT',     # VTK_INT,             # int32
        'uint32': 'MET_UINT',    # VTK_UNSIGNED_INT,    # uint32
        'float32': 'MET_FLOAT',   # VTK_FLOAT,           # float32
        'float64': 'MET_DOUBLE',  # VTK_DOUBLE,          # float64
    }
    # Utility functions to transform numpy arrays to vtkImageData and viceversa

    @staticmethod
    def numpy2vtkImage(nparray, spacing=(1., 1., 1.), origin=(0, 0, 0), deep=0, output=None):

        shape = numpy.shape(nparray)
        if(nparray.flags["FNC"]):

            order = "F"
            i = 0
            k = 2
        else:
            order = "C"
            i = 2
            k = 0

        nparray = nparray.ravel(order)
        vtkarray = numpy_support.numpy_to_vtk(
            num_array=nparray, deep=deep, array_type=numpy_support.get_vtk_array_type(nparray.dtype))
        vtkarray.SetName('vtkarray')

        if output is None:
            img_data = vtk.vtkImageData()
        else:
            if output.GetNumberOfPoints() > 0:
                raise ValueError(
                    'Output variable must be an empty vtkImageData object.')
            else:
                img_data = output

        img_data.GetPointData().AddArray(vtkarray)
        img_data.SetExtent(0, shape[i]-1, 0, shape[1]-1, 0, shape[k]-1)
        img_data.GetPointData().SetActiveScalars('vtkarray')
        img_data.SetOrigin(origin)
        img_data.SetSpacing(spacing)

        return img_data

    @staticmethod
    def vtk2numpy(imgdata, order=None):
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

        img_data.shape = (dims[2], dims[1], dims[0])

        if(order == 'F'):
            img_data = numpy.transpose(img_data, [2, 1, 0])
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
    def tiffStack2numpy(filename=None, indices=None, extent=None,
                        sampleRate=None, flatField=None, darkField=None,
                        filenames=None, tiffOrientation=1):
        '''Converts a stack of TIFF files to numpy array.

        filename must contain the whole path. The filename is supposed to be named and
        have a suffix with the ordinal file number, i.e. /path/to/projection_%03d.tif

        indices are the suffix, generally an increasing number

        Optionally extracts only a selection of the 2D images and (optionally)
        normalizes.
        '''

        if filename is not None and indices is not None:
            filenames = [filename % num for num in indices]
        return Converter._tiffStack2numpy(filenames=filenames, extent=extent,
                                          sampleRate=sampleRate,
                                          flatField=flatField,
                                          darkField=darkField)

    @staticmethod
    def tiffStack2numpyEnforceBounds(filename=None, indices=None,
                                     extent=None, sampleRate=None,
                                     flatField=None, darkField=None, filenames=None, tiffOrientation=1, bounds=(512, 512, 512)):
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

            stack_extent = img_ext[0:5] + (file_index,)
            size = stack_extent[1::2]
        else:
            size = extent[1::2]

        # Calculate re-sample rate
        sample_rate = tuple(
            map(lambda x, y: math.ceil(float(x)/y), size, bounds))

        # If a user has defined resample rate, check to see which has higher factor and keep that
        if sampleRate is not None:
            sampleRate = Converter.highest_tuple_element(
                sampleRate, sample_rate)
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
                         extent=None, sampleRate=None,
                         flatField=None, darkField=None, tiffOrientation=1):
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
            print("resampling %s" % (fn))
            reader.SetFileName(fn)
            reader.SetOrientationType(tiffOrientation)
            reader.Update()
            print(reader.GetOutput().GetScalarTypeAsString())
            if num == 0:

                # Extent
                if extent is None:
                    sliced = reader.GetOutput().GetExtent()
                    stack.SetExtent(sliced[0], sliced[1],
                                    sliced[2], sliced[3], 0, nreduced-1)

                    if sampleRate is not None:
                        voi.SetSampleRate(sampleRate)
                        ext = numpy.asarray(
                            [(sliced[2*i+1] - sliced[2*i])/sampleRate[i] for i in range(3)], dtype=int)
                        stack.SetExtent(0, ext[0], 0, ext[1], 0, nreduced - 1)
                else:
                    sliced = extent
                    voi.SetVOI(extent)

                    # Sample Rate
                    if sampleRate is not None:
                        voi.SetSampleRate(sampleRate)
                        ext = numpy.asarray(
                            [(sliced[2*i+1] - sliced[2*i])/sampleRate[i] for i in range(3)], dtype=int)
                        # print ("ext {0}".format(ext))
                        stack.SetExtent(0, ext[0], 0, ext[1], 0, nreduced-1)
                    else:
                        stack.SetExtent(
                            0, sliced[1] - sliced[0], 0, sliced[3]-sliced[2], 0, nreduced-1)

                # Flatfield
                if (flatField != None and darkField != None):
                    stack.AllocateScalars(vtk.VTK_FLOAT, 1)
                else:
                    stack.AllocateScalars(
                        reader.GetOutput().GetScalarType(), 1)

                print("Image Size: %d" % ((sliced[1]+1)*(sliced[3]+1)))
                stack_image = Converter.vtk2numpy(stack)
                print("Stack shape %s" % str(numpy.shape(stack_image)))

            if extent is not None or sampleRate is not None:
                voi.SetInputData(reader.GetOutput())
                voi.Update()
                img = voi.GetOutput()
            else:
                img = reader.GetOutput()

            theSlice = Converter.vtk2numpy(img)[0]
            if darkField != None and flatField != None:
                print("Try to normalize")
                # if numpy.shape(darkField) == numpy.shape(flatField) and numpy.shape(flatField) == numpy.shape(theSlice):
                theSlice = Converter.normalize(
                    theSlice, darkField, flatField, 0.01)
                print(theSlice.dtype)

            print("Slice shape %s" % str(numpy.shape(theSlice)))
            stack_image[num] = theSlice.copy()

        return stack_image

    @staticmethod
    def normalize(projection, dark, flat, def_val=0):
        a = (projection - dark)
        b = (flat-dark)
        with numpy.errstate(divide='ignore', invalid='ignore'):
            c = numpy.true_divide(a, b)
            c[~ numpy.isfinite(c)] = def_val  # set to not zero if 0/0
        return c

    @staticmethod
    def highest_tuple_element(user, calc):
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
        for u, c in zip(user, calc):
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
    __Spacing = (1., 1., 1.)

    def __init__(self):
        pass

    def SetInputData(self, array):
        if not isinstance(array, numpy.ndarray):
            raise ValueError('Input must be a NumPy array. Got', type(array))
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
            raise ValueError(
                'Spacing should be a list or a tuple. Got', type(value))
        if len(value) != len(self.__Array.shape):
            self.__Spacing = value
            self.Modified()

    @staticmethod
    def WriteMETAImageHeader(data_filename, header_filename, typecode, big_endian,
                             header_length, shape, spacing=(1., 1., 1.), origin=(0., 0., 0.)):
        '''Writes a NumPy array and a METAImage text header so that the npy file can be used as data file

        :param filename: name of the single file containing the data
        :param typecode: numpy typecode or metaimage type
        '''

        if typecode not in ['MET_CHAR',  'MET_UCHAR', 'MET_SHORT', 'MET_USHORT', 'MET_INT', 'MET_UINT', 'MET_FLOAT', 'MET_DOUBLE', 'MET_FLOAT', 'MET_DOUBLE']:
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
        header += 'ElementSpacing = {} {} {}\n'.format(
            spacing[0], spacing[1], spacing[2])
        header += 'Position = {} {} {}\n'.format(
            origin[0], origin[1], origin[2])
        # MSB (aka big-endian)
        # MSB = 'True' if descr['descr'][0] == '>' else 'False'
        header += 'ElementByteOrderMSB = {}\n'.format(big_endian)

        header += 'HeaderSize = {}\n'.format(header_length)
        header += 'ElementDataFile = {}'.format(os.path.abspath(data_filename))

        with open(header_filename, 'w') as hdr:
            hdr.write(header)

    @staticmethod
    def WriteNumpyAsMETAImage(array, filename, spacing=(1., 1., 1.), origin=(0., 0., 0.)):
        '''Writes a NumPy array and a METAImage text header so that the npy file can be used as data file'''
        # save the data as numpy
        datafname = os.path.abspath(filename) + '.npy'
        hdrfname = os.path.abspath(filename) + '.mhd'
        if (numpy.isfortran(array)):
            numpy.save(datafname, array)
        else:
            numpy.save(datafname, numpy.asfortranarray(array))
        npyhdr = parseNpyHeader(datafname)

        typecode = array.dtype.char
        print("typecode,", typecode)
        #r_type = Converter.numpy_dtype_char_to_MetaImageType[typecode]
        big_endian = 'True' if npyhdr['description']['descr'][0] == '>' else 'False'
        readshape = npyhdr['description']['shape']
        is_fortran = npyhdr['description']['fortran_order']
        if is_fortran:
            shape = list(readshape)
        else:
            shape = list(readshape)[::-1]
        header_length = npyhdr['header_length']

        cilNumpyMETAImageWriter.WriteMETAImageHeader(datafname, hdrfname, typecode, big_endian,
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


def WriteNumpyAsMETAImage(array, filename, spacing=(1., 1., 1.), origin=(0., 0., 0.)):
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
            'version_major': major,
            'version_minor': minor,
            'header_length': HEADER_LEN + 6 + 2 + HEADER_LEN_SIZE,
            'description': eval(descr)}


class cilBaseResampleReader(VTKPythonAlgorithmBase):
    '''vtkAlgorithm to load and resample a raw file to an approximate memory footprint


    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)

        self.__FileName = None
        self.__TargetSize = 256*256*256
        self.__IsFortran = False
        self.__BigEndian = False
        self.__FileHeaderLength = 0
        self.__BytesPerElement = 1
        self.__StoredArrayShape = None
        self.__OutputVTKType = None
        self.__NumpyTypeCode = None
        self.__RawTypeCode = None
        self.__MetaImageTypeCode = None
        self.__ElementSpacing = [1, 1, 1]
        self.__Origin = (0., 0., 0.)
        self.__IsAcquisitionData = False
        self.__SlicePerChunk = None
        self.__TempDir = None
        self.__ChunkReader = None

    def SetFileName(self, value):
        if not os.path.exists(value):
            raise ValueError('File does not exist!', value)

        if value != self.__FileName:
            self.__FileName = value
            self.Modified()

    def GetFileName(self):
        return self.__FileName

    def SetTargetSize(self, value):
        if not isinstance(value, int):
            raise ValueError('Expected an integer. Got {}', type(value))
        if not value == self.__TargetSize:
            self.__TargetSize = value
            self.Modified()

    def GetTargetSize(self):
        return self.__TargetSize

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

    def SetStoredArrayShape(self, value):
        if not isinstance(value, tuple):
            raise ValueError('Expected tuple, got {}'.format(type(value)))
        if len(value) != 3:
            raise ValueError(
                'Expected tuple of length 3, got {}'.format(len(value)))
        self.__StoredArrayShape = value

    def SetFileHeaderLength(self, value):
        if not isinstance(value, int):
            raise ValueError('Expected int, got {}'.format(type(value)))
        self.__FileHeaderLength = value

    def SetBytesPerElement(self, value):
        if not isinstance(value, int):
            raise ValueError('Expected int, got {}'.format(type(value)))
        self.__BytesPerElement = value

    def SetBigEndian(self, value):
        if not isinstance(value, bool):
            raise ValueError('Expected bool, got {}'.format(type(value)))
        self.__BigEndian = value

    def SetIsFortran(self, value):
        if not isinstance(value, bool):
            raise ValueError('Expected bool, got {}'.format(type(value)))
        self.__IsFortran = value

    def SetOutputVTKType(self, value):
        if value not in [vtk.VTK_SIGNED_CHAR, vtk.VTK_UNSIGNED_CHAR,  vtk.VTK_SHORT,  vtk.VTK_UNSIGNED_SHORT,
                         vtk.VTK_INT, vtk.VTK_UNSIGNED_INT,  vtk.VTK_FLOAT, vtk.VTK_DOUBLE, vtk.VTK_FLOAT,
                         vtk.VTK_DOUBLE]:
            raise ValueError("Unexpected Type:  {}".format(value))
        self.__OutputVTKType = value

    def SetNumpyTypeCode(self, value):
        if value not in ['b', 'B', 'h', 'H', 'i', 'I', 'f', 'd', 'F', 'D']:
            raise ValueError("Unexpected Type:  {}".format(value))
        self.__NumpyTypeCode = value
        self.SetMetaImageTypeCode(
            Converter.numpy_dtype_char_to_MetaImageType[value])

    def GetRawTypeCode(self):
        return self.__RawTypeCode

    def SetRawTypeCode(self, value):
        if value not in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64']:
            raise ValueError("Unexpected Type: got {}".format(value))
        self.__RawTypeCode = value
        self.SetMetaImageTypeCode(
            Converter.raw_dtype_char_to_MetaImageType[value])

    def GetMetaImageTypeCode(self):
        return self.__MetaImageTypeCode

    def SetMetaImageTypeCode(self, value):
        if value not in ['MET_CHAR',  'MET_UCHAR', 'MET_SHORT', 'MET_USHORT', 'MET_INT', 'MET_UINT', 'MET_FLOAT', 'MET_DOUBLE', 'MET_FLOAT', 'MET_DOUBLE']:
            raise ValueError("Unexpected Type:  {}".format(value))
        self.__MetaImageTypeCode = value
        self.SetOutputVTKType(Converter.MetaImageType_to_vtkType[value])

    def GetElementSpacing(self):
        return self.__ElementSpacing

    def SetElementSpacing(self, value):
        self.__ElementSpacing = value

    def SetOrigin(self, value):
        if not isinstance(value, tuple):
            raise ValueError('Expected a tuple. Got {}', type(value))

        if not value == self.__Origin:
            self.__Origin = value
            self.Modified()

    def GetOrigin(self):
        return self.__Origin

    def SetIsAcquisitionData(self, value):
        self.__IsAcquisitionData = value

    def GetIsAcquisitionData(self):
        return self.__IsAcquisitionData

    def ReadDataSetInfo(self):
        '''Tries to read info about dataset
        Will raise specific errors if inputs required for 
        file type are not set.'''
        if self.__StoredArrayShape is None:
            raise Exception("StoredArrayShape must be set.")
        
        if self.__OutputVTKType is None:
            raise Exception("Typecode must be set.")

    def _GetInternalChunkReader(self):
        tmpdir = tempfile.mkdtemp()
        self._SetTempDir(tmpdir)
        header_filename = os.path.join(tmpdir, "header.mhd")
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(header_filename)

        chunk_file_name = os.path.join(tmpdir, "chunk.raw")
        self.__ChunkFileName = chunk_file_name

        readshape = self.GetStoredArrayShape()
        is_fortran = self.GetIsFortran()

        if is_fortran:
            shape = list(readshape)
        else:
            shape = list(readshape)[::-1]

        chunk_shape = shape.copy()
        if self._GetSlicePerChunk() is not None:
            slice_per_chunk = self._GetSlicePerChunk()
        else:
            slice_per_chunk = shape[2]
        chunk_shape[2] = slice_per_chunk

        cilNumpyMETAImageWriter.WriteMETAImageHeader(
            chunk_file_name,
            header_filename,
            self.GetMetaImageTypeCode(),
            self.GetBigEndian(),
            0,
            tuple(chunk_shape),
            spacing=tuple(self.GetElementSpacing()),
            origin=self.GetOrigin()
        )
        self.__ChunkReader = reader
        return reader

    def UpdateChunkToRead(self, start_slice):

        # slice size in bytes
        nbytes = self.GetBytesPerElement()
        readshape = self.GetStoredArrayShape()
        is_fortran = self.GetIsFortran()

        if is_fortran:
            shape = list(readshape)
        else:
            shape = list(readshape)[::-1]
        slice_length = shape[1] * shape[0] * nbytes

        image_file = self.GetFileName()
        chunk_file_name = self.__ChunkFileName
        file_header_length = self.GetFileHeaderLength()
        slice_per_chunk = self._GetSlicePerChunk()

        with open(image_file, "rb") as image_file_object:
            if start_slice < 0:
                raise ValueError('{} ERROR: Start slice cannot be negative.'
                                 .format(self.__class__.__name__))
            chunk_location = file_header_length + start_slice*slice_length
            with open(chunk_file_name, "wb") as chunk_file_object:
                image_file_object.seek(chunk_location)
                chunk_length = slice_length*slice_per_chunk
                chunk = image_file_object.read(chunk_length)
                chunk_file_object.write(chunk)

    def _SetSlicePerChunk(self, value):
        self.__SlicePerChunk = value

    def _GetSlicePerChunk(self):
        return self.__SlicePerChunk

    def _GetTempDir(self):
        return self.__TempDir

    def _SetTempDir(self, folder):
        self.__TempDir = folder

    def RequestData(self, request, inInfo, outInfo):
        try:
            outData = vtk.vtkImageData.GetData(outInfo)

            if self.GetFileName() is None:
                raise Exception("FileName must be set.")

            self.ReadDataSetInfo()

            # get basic info
            readshape = self.GetStoredArrayShape()
            is_fortran = self.GetIsFortran()

            if is_fortran:
                shape = list(readshape)
            else:
                shape = list(readshape)[::-1]

            total_size = shape[0] * shape[1] * shape[2]

            max_size = self.GetTargetSize()

            if total_size < max_size:  # in this case we don't need to resample
                self._SetSlicePerChunk(shape[2])
                reader = self._GetInternalChunkReader()
                self.UpdateChunkToRead(0)
                reader.Modified()
                reader.Update()
                # print(reader.GetOutput().GetScalarComponentAsDouble(0, 0, 0, 0))
                outData.ShallowCopy(reader.GetOutput())

            else:

                # scaling is going to be similar in every axis
                # (xy the same, z possibly different)
                if not self.GetIsAcquisitionData():
                    xy_axes_magnification = np.power(max_size/total_size, 1/3)
                    slice_per_chunk = np.int(1/xy_axes_magnification)
                else:
                    slice_per_chunk = 1
                    xy_axes_magnification = np.power(max_size/total_size, 1/2)

                self._SetSlicePerChunk(slice_per_chunk)

                # print("Slice per chunk: ", slice_per_chunk)

                # indices of the first slice per chunk
                # we will read in slice_per_chunk slices at a time
                start_sliceno_in_chunks = [i for i in range(
                    0, shape[2], slice_per_chunk)]

                num_chunks = len(start_sliceno_in_chunks)

                z_axis_magnification = num_chunks / (shape[2])

                target_image_shape = (int(xy_axes_magnification * shape[0]),
                                      int(xy_axes_magnification * shape[1]),
                                      num_chunks)

                resampler = vtk.vtkImageReslice()

                element_spacing = self.GetElementSpacing()

                resampler.SetOutputSpacing(
                    element_spacing[0]/xy_axes_magnification,
                    element_spacing[1]/xy_axes_magnification,
                    element_spacing[2]/z_axis_magnification)
                # resampled data
                resampled_image = outData

                resampled_image.SetExtent(0, target_image_shape[0]-1,
                                          0, target_image_shape[1]-1,
                                          0, target_image_shape[2]-1)

                resampled_image.SetSpacing(
                    element_spacing[0]/xy_axes_magnification,
                    element_spacing[1]/xy_axes_magnification,
                    element_spacing[2]/z_axis_magnification)

                new_spacing = [element_spacing[0]/xy_axes_magnification,
                               element_spacing[1]/xy_axes_magnification,
                               element_spacing[2]/z_axis_magnification]

                original_origin = self.GetOrigin()
                new_origin = tuple([(s-1)/2 + original_origin[i]
                                   for i, s in enumerate(new_spacing)])

                resampled_image.SetOrigin(new_origin)

                resampled_image.AllocateScalars(self.GetOutputVTKType(), 1)

                reader = self._GetInternalChunkReader()

                resampler.SetInputData(reader.GetOutput())

                # process each chunk
                for i, start_sliceno in enumerate(start_sliceno_in_chunks):

                    self.UpdateChunkToRead(start_sliceno)

                    reader.Modified()
                    reader.Update()
                    # print(i, reader.GetOutput().GetScalarComponentAsDouble(0,0,0,0))

                    # change the extent of the resampled image
                    extent = (0, target_image_shape[0]-1,
                              0, target_image_shape[1]-1,
                              i, i)

                    resampler.SetOutputExtent(extent)
                    resampler.Update()
                    # print(i, resampler.GetOutput().GetScalarComponentAsDouble(0,0,i,0))

                    ################# vtk way ####################
                    resampled_image.CopyAndCastFrom(
                        resampler.GetOutput(), extent)
                    self.UpdateProgress(i / num_chunks)
        except Exception as e:
            raise Exception(e)

        finally:
            if self._GetTempDir() is not None:
                shutil.rmtree(self._GetTempDir())

        return 1

    def GetOutput(self):
        return self.GetOutputDataObject(0)


class cilNumpyResampleReader(cilBaseResampleReader):
    '''vtkAlgorithm to load and resample a numpy file to an approximate memory footprint


    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilNumpyResampleReader, self).__init__()

        self.__FileName = None

    def ReadNpyHeader(self):
        # extract info from the npy header
        descr = parseNpyHeader(self.__FileName)
        # find the typecode of the data and the number of bytes per pixel
        typecode = ''
        nbytes = 0
        for t in [np.uint8, np.int8, np.int16, np.uint16, np.int32, np.uint32, np.float16, np.float32, np.float64]:
            array_descr = descr['description']['descr'][1:]
            if array_descr == np.dtype(t).descr[0][1][1:]:
                typecode = np.dtype(t).char
                nbytes = Converter.numpy_dtype_char_to_bytes[typecode]
                break

        big_endian = True if descr['description']['descr'][0] == '>' else False
        readshape = descr['description']['shape']
        is_fortran = descr['description']['fortran_order']
        file_header_length = descr['header_length']

        self.SetIsFortran(is_fortran)
        self.SetBigEndian(big_endian)
        self.SetFileHeaderLength(file_header_length)
        self.SetBytesPerElement(nbytes)
        self.SetStoredArrayShape(readshape)
        self.SetMetaImageTypeCode(
            Converter.numpy_dtype_char_to_MetaImageType[typecode])

        self.Modified()

    def SetFileName(self, value):
        # in the case of an mha file, data is stored in the same file.
        if value != 'LOCAL':
            if not os.path.exists(value):
                raise ValueError('File does not exist!', value)

        if value != self.__FileName:
            self.__FileName = value
            self.ReadNpyHeader()
            self.Modified()

    def GetFileName(self):
        return self.__FileName

    def ReadDataSetInfo(self):
        self.ReadNpyHeader()


class cilHDF5ResampleReader(cilBaseResampleReader):

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilHDF5ResampleReader, self).__init__()
        self.__FileName = None
        self.__DatasetName = None
        self.__IsFortran = True

    def SetDatasetName(self, value):
        if value != self.__DatasetName:
            self.__DatasetName = value
            if self.GetFileName() is not None:
                self.ReadDataSetInfo()

    def SetFileName(self, value):
        if value != self.__FileName:
            self.__FileName = value
            if self.GetDatasetName() is not None:
                self.ReadDataSetInfo()

    def GetIsFortran(self):
        return self.__IsFortran 

    def GetFileName(self):
        return self.__FileName

    def GetDatasetName(self):
        return self.__DatasetName

    def ReadDataSetInfo(self):
        reader = HDF5Reader()
        reader.SetFileName(self.GetFileName())
        if self.GetDatasetName() is not None:
            reader.SetDatasetName(self.GetDatasetName())
        else:
            raise Exception("DataSetName must be set.")
        shape = reader.GetDimensions()
        self.SetStoredArrayShape(shape)
        # get the datatype:
        datatype = reader.GetDataType()
        typecode = np.dtype(datatype).char
        nbytes = Converter.numpy_dtype_char_to_bytes[typecode]
        self.SetBytesPerElement(nbytes)
        self.SetOutputVTKType(
            Converter.numpy_dtype_char_to_vtkType[typecode])

    def _GetInternalChunkReader(self):
        reader = HDF5Reader()
        reader.SetFileName(self.GetFileName())
        if self.GetDatasetName() is not None:
            reader.SetDatasetName(self.GetDatasetName())
        else:
            raise Exception("DataSetName must be set.")
        self.SetOrigin(reader.GetOrigin())
        # Here we read just the chunk from the hdf5 file:
        cropped_reader = HDF5SubsetReader()
        cropped_reader.SetInputConnection(reader.GetOutputPort())
        dims = self.GetStoredArrayShape()
        # Set default extent to full extent:
        cropped_reader.SetUpdateExtent(
            (0, dims[0]-1, 0, dims[1]-1, 0, dims[2]-1))
        self.__ChunkReader = cropped_reader
        return cropped_reader

    def UpdateChunkToRead(self, start_slice):
        slice_per_chunk = self._GetSlicePerChunk()
        end_slice = start_slice + slice_per_chunk - 1
        if start_slice < 0:
            raise ValueError('{} ERROR: Start slice cannot be negative.'
                             .format(self.__class__.__name__))
        dims = self.GetStoredArrayShape()
        self.__ChunkReader.SetUpdateExtent(
            (0, dims[0]-1, 0, dims[1]-1, start_slice, end_slice))


class cilMetaImageResampleReader(cilBaseResampleReader):
    '''vtkAlgorithm to load and resample a metaimage file to an approximate memory footprint


    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilMetaImageResampleReader, self).__init__()

        self.__FileName = None
        self.__CompressedData = False
        self.__ElementSpacing = [1, 1, 1]

    def ReadMetaImageHeader(self):

        header_length = 0
        with open(self.__FileName, 'rb') as f:
            for line in f:
                header_length += len(line)
                line = str(line, encoding='utf-8').strip()
                if 'BinaryDataByteOrderMSB' in line:
                    if str(line).split('= ')[-1] == "True":
                        self.SetBigEndian(True)
                    else:
                        self.SetBigEndian(False)
                elif 'Offset' in line:
                    origin = line.split('= ')[-1].split(' ')[:3]
                    origin[2].strip()
                    for i in range(0, len(origin)):
                        origin[i] = float(origin[i])
                    self.SetOrigin(tuple(origin))
                    # print(self.GetBigEndian())
                elif 'ElementSpacing' in line:
                    spacing = line.split('= ')[-1].split(' ')[:3]
                    spacing[2].strip()
                    for i in range(0, len(spacing)):
                        spacing[i] = float(spacing[i])
                    self.SetElementSpacing(spacing)
                    # print("Spacing", spacing)
                elif 'DimSize' in line:
                    shape = line.split('= ')[-1].split(' ')[:3]
                    shape[2].strip()
                    for i in range(0, len(shape)):
                        shape[i] = int(shape[i])
                    self.SetStoredArrayShape(tuple(shape))
                    # print("DIMSIZE", self.GetStoredArrayShape())
                elif 'ElementType' in line:
                    typecode = line.split('= ')[-1]
                    self.SetMetaImageTypeCode(typecode)
                    # print(self.GetMetaImageTypeCode())
                elif 'CompressedData' in line:
                    compressed = line.split('= ')[-1]
                    self.SetCompressedData(compressed)
                    if(self.GetCompressedData() == "True"):
                        print("Cannot resample compressed image")
                        return

                elif 'HeaderSize' in line:
                    header_size = line.split('= ')[-1]
                    self.SetFileHeaderLength(int(header_size))

                elif 'ElementDataFile' in line:  # signifies end of header
                    element_data_file = line.split('= ')[-1]
                    if element_data_file != 'LOCAL':  # then we have an mhd file with data in another file
                        file_path = os.path.dirname(self.__FileName)
                        element_data_file = os.path.join(
                            file_path, element_data_file)
                        # print("Filename: ", element_data_file)
                        self.__FileName = element_data_file
                    else:
                        self.SetFileHeaderLength(header_length)
                    break

        self.SetIsFortran(True)
        self.SetBytesPerElement(
            Converter.MetaImageType_to_bytes[self.GetMetaImageTypeCode()])

        self.Modified()

    def SetFileName(self, value):
        # in the case of an mha file, data is stored in the same file.
        if value != 'LOCAL':
            if not os.path.exists(value):
                raise ValueError('File does not exist!', value)

        if value != self.__FileName:
            self.__FileName = value
            self.ReadMetaImageHeader()
            self.Modified()

    def GetFileName(self):
        return self.__FileName

    def GetCompressedData(self):
        return self.__CompressedData

    def SetCompressedData(self, value):
        self.__CompressedData = value

    def ReadDataSetInfo(self):
        self.ReadMetaImageHeader()


class cilBaseCroppedReader(VTKPythonAlgorithmBase):
    '''vtkAlgorithm to crop in the z direction
    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)

        self.__FileName = None
        self.__IsFortran = False
        self.__BigEndian = False
        self.__FileHeaderLength = 0
        self.__BytesPerElement = 1
        self.__StoredArrayShape = None
        self.__OutputVTKType = None
        self.__NumpyTypeCode = None
        self.__MetaImageTypeCode = None
        self.__TargetZExtent = (0, 0)
        self.__Origin = (0, 0, 0)
        self.__ElementSpacing = [1, 1, 1]

    def SetFileName(self, value):
        '''Sets the value at which the mask is active'''
        if not os.path.exists(value):
            raise ValueError('File does not exist!', value)

        if value != self.__FileName:
            self.__FileName = value
            self.Modified()

    def GetFileName(self):
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
        if not isinstance(value, tuple):
            raise ValueError('Expected tuple, got {}'.format(type(value)))
        if len(value) != 3:
            raise ValueError(
                'Expected tuple of length 3, got {}'.format(len(value)))
        self.__StoredArrayShape = value

    def SetFileHeaderLength(self, value):
        if not isinstance(value, int):
            raise ValueError('Expected int, got {}'.format(type(value)))
        self.__FileHeaderLength = value

    def SetBytesPerElement(self, value):
        if not isinstance(value, int):
            raise ValueError('Expected int, got {}'.format(type(value)))
        self.__BytesPerElement = value

    def SetBigEndian(self, value):
        if not isinstance(value, bool):
            raise ValueError('Expected bool, got {}'.format(type(value)))
        self.__BigEndian = value

    def SetIsFortran(self, value):
        if not isinstance(value, bool):
            raise ValueError('Expected bool, got {}'.format(type(value)))
        self.__IsFortran = value

    def SetOutputVTKType(self, value):
        if value not in [vtk.VTK_SIGNED_CHAR, vtk.VTK_UNSIGNED_CHAR,  vtk.VTK_SHORT,  vtk.VTK_UNSIGNED_SHORT,
                         vtk.VTK_INT, vtk.VTK_UNSIGNED_INT,  vtk.VTK_FLOAT, vtk.VTK_DOUBLE, vtk.VTK_FLOAT,
                         vtk.VTK_DOUBLE]:
            raise ValueError("Unexpected Type:  {}".format(value))
        self.__OutputVTKType = value

    def SetNumpyTypeCode(self, value):
        if value not in ['b', 'B', 'h', 'H', 'i', 'I', 'f', 'd', 'F', 'D']:
            raise ValueError("Unexpected Type:  {}".format(value))
        self.__NumpyTypeCode = value
        self.SetMetaImageTypeCode(
            Converter.numpy_dtype_char_to_MetaImageType[value])

    def SetRawTypeCode(self, value):
        if value not in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64']:
            raise ValueError("Unexpected Type: got {}".format(value))
        self.__RawTypeCode = value
        self.SetMetaImageTypeCode(
            Converter.raw_dtype_char_to_MetaImageType[value])

    def GetMetaImageTypeCode(self):
        return self.__MetaImageTypeCode

    def SetMetaImageTypeCode(self, value):
        if value not in ['MET_CHAR',  'MET_UCHAR', 'MET_SHORT', 'MET_USHORT', 'MET_INT', 'MET_UINT', 'MET_FLOAT', 'MET_DOUBLE', 'MET_FLOAT', 'MET_DOUBLE']:
            raise ValueError("Unexpected Type:  {}".format(value))
        self.__MetaImageTypeCode = value
        self.SetOutputVTKType(Converter.MetaImageType_to_vtkType[value])

    def SetTargetZExtent(self, value):
        if not isinstance(value, tuple):
            raise ValueError('Expected a tuple. Got {}', type(value))

        if not value == self.__TargetZExtent:
            self.__TargetZExtent = value
            self.Modified()

    def GetTargetZExtent(self):
        return self.__TargetZExtent

    def SetOrigin(self, value):
        if not isinstance(value, tuple):
            raise ValueError('Expected a tuple. Got {}', type(value))

        if not value == self.__Origin:
            self.__Origin = value
            self.Modified()

    def GetOrigin(self):
        return self.__Origin

    def GetElementSpacing(self):
        return self.__ElementSpacing

    def SetElementSpacing(self, value):
        self.__ElementSpacing = value

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

        slice_length = shape[1] * shape[0] * nbytes

        tmpdir = tempfile.mkdtemp()
        header_filename = os.path.join(tmpdir, "header.mhd")
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(header_filename)

        # in this case we don't need to resample
        if self.GetTargetZExtent()[1] >= shape[2]:
            try:
                # print("Don't resample")

                chunk_file_name = os.path.join(tmpdir, "chunk.raw")

                cilNumpyMETAImageWriter.WriteMETAImageHeader(chunk_file_name,
                                                             header_filename,
                                                             self.GetMetaImageTypeCode(),
                                                             big_endian,
                                                             0,
                                                             tuple(shape),
                                                             spacing=tuple(
                                                                 self.GetElementSpacing()),
                                                             origin=self.GetOrigin())

                image_file = self.GetFileName()

                with open(image_file, "rb") as image_file_object:
                    end_slice = shape[2]
                    chunk_location = file_header_length
                    with open(chunk_file_name, "wb") as chunk_file_object:
                        image_file_object.seek(chunk_location)
                        chunk_length = slice_length*end_slice
                        chunk = image_file_object.read(chunk_length)
                        chunk_file_object.write(chunk)

                reader.Modified()
                reader.Update()
                print(reader.GetOutput().GetScalarComponentAsDouble(0, 0, 0, 0))
                outData.ShallowCopy(reader.GetOutput())

            finally:
                os.remove(header_filename)
                os.remove(chunk_file_name)
                os.rmdir(tmpdir)

            return 1

        try:
            shape[2] = self.GetTargetZExtent()[1] + 1

            chunk_file_name = os.path.join(tmpdir, "chunk.raw")

            cilNumpyMETAImageWriter.WriteMETAImageHeader(chunk_file_name,
                                                         header_filename,
                                                         self.GetMetaImageTypeCode(),
                                                         big_endian,
                                                         0,
                                                         tuple(shape),
                                                         spacing=tuple(
                                                             self.GetElementSpacing()),
                                                         origin=self.GetOrigin())

            image_file = self.GetFileName()

            chunk_location = file_header_length + \
                (self.GetTargetZExtent()[0]) * slice_length

            with open(chunk_file_name, "wb") as chunk_file_object:
                with open(image_file, "rb") as image_file_object:
                    image_file_object.seek(chunk_location)
                    chunk_length = (self.GetTargetZExtent()[
                                    1] - self.GetTargetZExtent()[0] + 1) * slice_length
                    chunk = image_file_object.read(chunk_length)
                    chunk_file_object.write(chunk)

            reader.Modified()
            reader.Update()

            Data = vtk.vtkImageData()
            extent = (0, shape[0]-1, 0, shape[1]-1,
                      self.GetTargetZExtent()[0], self.GetTargetZExtent()[1])
            Data.SetExtent(extent)
            Data.SetSpacing(self.GetElementSpacing())
            Data.SetOrigin(self.GetOrigin())
            Data.AllocateScalars(self.GetOutputVTKType(), 1)

            read_data = reader.GetOutput()
            read_data.SetExtent(extent)

            Data.CopyAndCastFrom(read_data, extent)
            outData.ShallowCopy(Data)

        except Exception as e:
            print("Exception", e)
        finally:
            os.remove(header_filename)
            os.remove(chunk_file_name)
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

        self.__FileName = None
        self.__TargetSize = 256*256*256
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
        # self.SetNumpyTypeCode(typecode)

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

    def GetMetaImageTypeCode(self):
        self.ReadNpyHeader()
        return self.__MetaImageTypeCode

    def GetNumpyTypeCode(self):
        self.ReadNpyHeader()
        return self.__NumpyTypeCode


class cilMetaImageCroppedReader(cilBaseCroppedReader):
    '''vtkAlgorithm to load and resample a metaimage file to an approximate memory footprint


    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilMetaImageCroppedReader, self).__init__()

        self.__FileName = None
        self.__TargetSize = 256*256*256
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
                line = str(line, encoding='utf-8').strip()
                if 'BinaryDataByteOrderMSB' in line:
                    if str(line).split('= ')[-1] == "True":
                        self.SetBigEndian(True)
                    else:
                        self.SetBigEndian(False)
                    # print(self.GetBigEndian())
                elif 'Offset' in line:
                    origin = line.split('= ')[-1].split(' ')[:3]
                    origin[2].strip()
                    for i in range(0, len(origin)):
                        origin[i] = float(origin[i])
                    self.SetOrigin(tuple(origin))
                elif 'ElementSpacing' in line:
                    spacing = line.split('= ')[-1].split(' ')[:3]
                    spacing[2].strip()
                    for i in range(0, len(spacing)):
                        spacing[i] = float(spacing[i])
                    self.SetElementSpacing(spacing)
                    # print("Spacing", spacing)
                elif 'DimSize' in line:
                    shape = line.split('= ')[-1].split(' ')[:3]
                    shape[2].strip()
                    for i in range(0, len(shape)):
                        shape[i] = int(shape[i])
                    self.SetStoredArrayShape(tuple(shape))
                    # print(self.GetStoredArrayShape())
                elif 'ElementType' in line:
                    typecode = line.split('= ')[-1]
                    self.SetMetaImageTypeCode(typecode)
                    # print(self.GetMetaImageTypeCode())
                elif 'CompressedData' in line:
                    compressed = line.split('= ')[-1]
                    self.SetCompressedData(compressed)
                    if(self.GetCompressedData() == "True"):
                        print("Cannot resample compressed image")
                        return

                elif 'HeaderSize' in line:
                    header_size = line.split('= ')[-1]
                    self.SetFileHeaderLength(int(header_size))

                elif 'ElementDataFile' in line:  # signifies end of header
                    element_data_file = line.split('= ')[-1]
                    if element_data_file != 'LOCAL':  # then we have an mhd file with data in another file
                        file_path = os.path.dirname(self.__FileName)
                        element_data_file = os.path.join(
                            file_path, element_data_file)
                        # print("Filename: ", element_data_file)
                        self.__FileName = element_data_file
                    else:
                        self.SetFileHeaderLength(header_length)
                    break

        self.SetIsFortran(True)
        self.SetBytesPerElement(
            Converter.MetaImageType_to_bytes[self.GetMetaImageTypeCode()])

        self.Modified()

        # self.Modified()

    def SetFileName(self, value):
        # in the case of an mha file, data is stored in the same file.
        if value != 'LOCAL':
            if not os.path.exists(value):
                raise ValueError('File does not exist!', value)

        if value != self.__FileName:
            self.__FileName = value
            self.Modified()
            self.ReadMetaImageHeader()

    def GetFileName(self):
        return self.__FileName

    def GetCompressedData(self):
        return self.__CompressedData

    def SetCompressedData(self, value):
        self.__CompressedData = value

class cilHDF5CroppedReader(cilBaseCroppedReader):
    '''vtkAlgorithm to load and resample a numpy file to an approximate memory footprint

    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilHDF5CroppedReader, self).__init__()

        self.__FileName = None
        self.__DatasetName = None
        # This is because the HDF5Reader already swaps the order:
        self.__IsFortran = True
        self.__StoredArrayShape = None
        self.__OutputVTKType = None
        self.__TargetExtent = None

    def SetTargetExtent(self, value):
        self.__TargetExtent = value

    def GetTargetExtent(self):
        return self.__TargetExtent

    def SetDatasetName(self, value):
        print(value, self.__DatasetName)
        if value != self.__DatasetName:
            self.__DatasetName = value
            if self.GetFileName() is not None:
                self.ReadDataSetInfo()

    def SetFileName(self, value):
        if value != self.__FileName:
            self.__FileName = value
            if self.GetDatasetName() is not None:
                self.ReadDataSetInfo()

    def GetFileName(self):
        return self.__FileName

    def GetDatasetName(self):
        return self.__DatasetName

    def ReadDataSetInfo(self):
        reader = HDF5Reader()
        reader.SetFileName(self.GetFileName())
        if self.GetDatasetName() is not None:
            reader.SetDatasetName(self.GetDatasetName())
        shape = reader.GetDimensions()
        self.SetStoredArrayShape(shape)
        # get the datatype:
        datatype = reader.GetDataType()
        typecode = np.dtype(datatype).char
        nbytes = Converter.numpy_dtype_char_to_bytes[typecode]
        self.SetBytesPerElement(nbytes)
        self.SetOutputVTKType(
            Converter.numpy_dtype_char_to_vtkType[typecode])

    def GetStoredArrayShape(self):
        self.ReadDataSetInfo()
        return self.__StoredArrayShape

    def GetBytesPerElement(self):
        return self.__BytesPerElement

    def GetIsFortran(self):
        return self.__IsFortran

    def GetOutputVTKType(self):
        self.ReadDataSetInfo()
        return self.__OutputVTKType

    def RequestData(self, request, inInfo, outInfo):
        outData = vtk.vtkImageData.GetData(outInfo)

        full_reader = HDF5Reader()
        full_reader.SetFileName(self.GetFileName())
        full_reader.SetDatasetName(self.GetDatasetName())
        reader = HDF5SubsetReader()
        reader.SetInputConnection(full_reader.GetOutputPort())
        if self.GetTargetExtent() is None:
            extent = [0, -1, 0, -1, self.GetTargetZExtent[0], self.GetTargetZExtent[1]]
        else:
            extent = self.GetTargetExtent()
        reader.SetUpdateExtent(extent)

        read_data = reader.GetOutput()
        outData.ShallowCopy(read_data)


if __name__ == '__main__':
    '''this represent a good base to perform a test for the numpy-metaimage writer'''
    dimX = 128
    dimY = 64
    dimZ = 32
    # a = numpy.zeros((dimX,dimY,dimZ), dtype=numpy.uint16)
    a = numpy.random.randint(0, size=(dimX, dimY, dimZ),
                             high=127,  dtype=numpy.uint16)
    # for x in range(a.shape[0]):
    #    for y in range(a.shape[1]):
    #        for z in range(a.shape[2]):
    #            a[x][y][z] = x + a.shape[0] * y + a.shape[0]*a.shape[1]*z
    for z in range(a.shape[2]):
        b = z * numpy.ones((a.shape[0], a.shape[1]), dtype=numpy.uint8)
        a[:, :, z] = b.copy()

    #arfn = os.path.abspath('C:/Users/ofn77899/Documents/Projects/CCPi/GitHub/CCPi-Simpleflex/data/head.npy')
    arfn = 'test'
    WriteNumpyAsMETAImage(a, arfn)
    hdrdescr = parseNpyHeader(arfn+'.npy')

    #a = numpy.load(arfn+'.npy')

    #import matplotlib.pyplot as plt
    # plt.imshow(a[10,:,:])
    # plt.show()

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
                    v2 = numpy.uint8(
                        reader.GetOutput().GetScalarComponentAsFloat(x, y, z, 0))
                    # print ("value check {} {} {},".format((x,y,z) ,v1,v2))
                    is_same = v1 == v2
                    if not is_same:
                        raise ValueError(
                            'arrays do not match', v1, v2, x, y, z)
        print('YEEE array match!')
