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

    # Converting to vtk: --------------------------------

    MetaImageType_to_vtkType = {
        'MET_CHAR': vtk.VTK_SIGNED_CHAR,  # int8
        'MET_UCHAR': vtk.VTK_UNSIGNED_CHAR,  # uint8
        'MET_SHORT': vtk.VTK_SHORT,  # int16
        'MET_USHORT': vtk.VTK_UNSIGNED_SHORT,  # uint16
        'MET_INT': vtk.VTK_INT,  # int32
        'MET_UINT': vtk.VTK_UNSIGNED_INT,  # uint32
        'MET_FLOAT': vtk.VTK_FLOAT,  # float32
        'MET_DOUBLE': vtk.VTK_DOUBLE,  # float64
    }

    dtype_name_to_vtkType = {
        'int8': vtk.VTK_SIGNED_CHAR,
        'uint8': vtk.VTK_UNSIGNED_CHAR,
        'int16': vtk.VTK_SHORT,
        'uint16': vtk.VTK_UNSIGNED_SHORT,
        'int32': vtk.VTK_INT,
        'uint32': vtk.VTK_UNSIGNED_INT,
        'float32': vtk.VTK_FLOAT,
        'float64': vtk.VTK_DOUBLE,
    }

    # Converting from vtk to bytes: -------------------------------------------
    vtkType_to_bytes = {
        vtk.VTK_SIGNED_CHAR: 1,  # int8
        vtk.VTK_UNSIGNED_CHAR: 1,  # uint8
        vtk.VTK_SHORT: 2,  # int16
        vtk.VTK_UNSIGNED_SHORT: 2,  # uint16
        vtk.VTK_INT: 4,  # int32
        vtk.VTK_UNSIGNED_INT: 4,  # uint32
        vtk.VTK_FLOAT: 4,  # float32
        vtk.VTK_DOUBLE: 8,  # float64
    }

    dtype_name_to_MetaImageType = {
        'int8': 'MET_CHAR',  # VTK_SIGNED_CHAR,     # int8
        'uint8': 'MET_UCHAR',  # VTK_UNSIGNED_CHAR,   # uint8
        'int16': 'MET_SHORT',  # VTK_SHORT,           # int16
        'uint16': 'MET_USHORT',  # VTK_UNSIGNED_SHORT,  # uint16
        'int32': 'MET_INT',  # VTK_INT,             # int32
        'uint32': 'MET_UINT',  # VTK_UNSIGNED_INT,    # uint32
        'float32': 'MET_FLOAT',  # VTK_FLOAT,           # float32
        'float64': 'MET_DOUBLE',  # VTK_DOUBLE,          # float64
    }

    # Utility functions to transform numpy arrays to vtkImageData and viceversa

    @staticmethod
    def numpy2vtkImage(nparray, spacing=(1., 1., 1.), origin=(0, 0, 0), deep=0, output=None):

        shape = numpy.shape(nparray)
        if (nparray.flags["FNC"]):

            order = "F"
            i = 0
            k = 2
        else:
            order = "C"
            i = 2
            k = 0

        nparray = nparray.ravel(order)
        vtkarray = numpy_support.numpy_to_vtk(num_array=nparray,
                                              deep=deep,
                                              array_type=numpy_support.get_vtk_array_type(nparray.dtype))
        vtkarray.SetName('vtkarray')

        if output is None:
            img_data = vtk.vtkImageData()
        else:
            if output.GetNumberOfPoints() > 0:
                raise ValueError('Output variable must be an empty vtkImageData object.')
            else:
                img_data = output

        img_data.GetPointData().AddArray(vtkarray)
        img_data.SetExtent(0, shape[i] - 1, 0, shape[1] - 1, 0, shape[k] - 1)
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
        img_data = numpy_support.vtk_to_numpy(imgdata.GetPointData().GetScalars())

        dims = imgdata.GetDimensions()
        # print ("vtk2numpy: VTKImageData dims {0}".format(dims))

        # print("chosen order ", order)

        img_data.shape = (dims[2], dims[1], dims[0])

        if (order == 'F'):
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
    def tiffStack2numpy(filename=None,
                        indices=None,
                        extent=None,
                        sampleRate=None,
                        flatField=None,
                        darkField=None,
                        filenames=None,
                        tiffOrientation=1):
        '''Converts a stack of TIFF files to numpy array.

        filename must contain the whole path. The filename is supposed to be named and
        have a suffix with the ordinal file number, i.e. /path/to/projection_%03d.tif

        indices are the suffix, generally an increasing number

        Optionally extracts only a selection of the 2D images and (optionally)
        normalizes.
        '''

        if filename is not None and indices is not None:
            filenames = [filename % num for num in indices]
        return Converter._tiffStack2numpy(filenames=filenames,
                                          extent=extent,
                                          sampleRate=sampleRate,
                                          flatField=flatField,
                                          darkField=darkField)

    @staticmethod
    def tiffStack2numpyEnforceBounds(filename=None,
                                     indices=None,
                                     extent=None,
                                     sampleRate=None,
                                     flatField=None,
                                     darkField=None,
                                     filenames=None,
                                     tiffOrientation=1,
                                     bounds=(512, 512, 512)):
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

            stack_extent = img_ext[0:5] + (file_index, )
            size = stack_extent[1::2]
        else:
            size = extent[1::2]

        # Calculate re-sample rate
        sample_rate = tuple(map(lambda x, y: math.ceil(float(x) / y), size, bounds))

        # If a user has defined resample rate, check to see which has higher factor and keep that
        if sampleRate is not None:
            sampleRate = Converter.highest_tuple_element(sampleRate, sample_rate)
        else:
            sampleRate = sample_rate

        # Re-sample input filelist
        list_sample_index = sampleRate[2]
        filenames = filenames[::list_sample_index]

        return Converter._tiffStack2numpy(filenames=filenames,
                                          extent=extent,
                                          sampleRate=sampleRate,
                                          flatField=flatField,
                                          darkField=darkField)

    @staticmethod
    def _tiffStack2numpy(filenames, extent=None, sampleRate=None, flatField=None, darkField=None, tiffOrientation=1):
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
                    stack.SetExtent(sliced[0], sliced[1], sliced[2], sliced[3], 0, nreduced - 1)

                    if sampleRate is not None:
                        voi.SetSampleRate(sampleRate)
                        ext = numpy.asarray([(sliced[2 * i + 1] - sliced[2 * i]) / sampleRate[i] for i in range(3)],
                                            dtype=int)
                        stack.SetExtent(0, ext[0], 0, ext[1], 0, nreduced - 1)
                else:
                    sliced = extent
                    voi.SetVOI(extent)

                    # Sample Rate
                    if sampleRate is not None:
                        voi.SetSampleRate(sampleRate)
                        ext = numpy.asarray([(sliced[2 * i + 1] - sliced[2 * i]) / sampleRate[i] for i in range(3)],
                                            dtype=int)
                        # print ("ext {0}".format(ext))
                        stack.SetExtent(0, ext[0], 0, ext[1], 0, nreduced - 1)
                    else:
                        stack.SetExtent(0, sliced[1] - sliced[0], 0, sliced[3] - sliced[2], 0, nreduced - 1)

                # Flatfield
                if (flatField != None and darkField != None):
                    stack.AllocateScalars(vtk.VTK_FLOAT, 1)
                else:
                    stack.AllocateScalars(reader.GetOutput().GetScalarType(), 1)

                print("Image Size: %d" % ((sliced[1] + 1) * (sliced[3] + 1)))
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
                theSlice = Converter.normalize(theSlice, darkField, flatField, 0.01)
                print(theSlice.dtype)

            print("Slice shape %s" % str(numpy.shape(theSlice)))
            stack_image[num] = theSlice.copy()

        return stack_image

    @staticmethod
    def normalize(projection, dark, flat, def_val=0):
        a = (projection - dark)
        b = (flat - dark)
        with numpy.errstate(divide='ignore', invalid='ignore'):
            c = numpy.true_divide(a, b)
            c[~numpy.isfinite(c)] = def_val  # set to not zero if 0/0
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
            raise ValueError('Spacing should be a list or a tuple. Got', type(value))
        if len(value) != len(self.__Array.shape):
            self.__Spacing = value
            self.Modified()

    @staticmethod
    def WriteMETAImageHeader(data_filename,
                             header_filename,
                             typecode,
                             big_endian,
                             header_length,
                             shape,
                             spacing=(1., 1., 1.),
                             origin=(0., 0., 0.)):
        '''Writes a NumPy array and a METAImage text header so that the npy file can be used as data file

        Parameters
        -----------
        filename
            name of the single file containing the data
        typecode
            metaimage typecode, or one of : 
            ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64']
        shape
            the shape of the data in data_filename:
            NOTE: if the data is not stored in fortran order then you must set this to shape[::-1]

        '''

        if typecode not in Converter.MetaImageType_to_vtkType.keys():
            ar_type = Converter.dtype_name_to_MetaImageType[typecode]
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
        typecode = str(array.dtype)
        big_endian = 'True' if npyhdr['description']['descr'][0] == '>' else 'False'
        readshape = npyhdr['description']['shape']
        is_fortran = npyhdr['description']['fortran_order']
        if is_fortran:
            shape = list(readshape)
        else:
            shape = list(readshape)[::-1]
        header_length = npyhdr['header_length']

        cilNumpyMETAImageWriter.WriteMETAImageHeader(datafname,
                                                     hdrfname,
                                                     typecode,
                                                     big_endian,
                                                     header_length,
                                                     shape,
                                                     spacing=spacing,
                                                     origin=origin)


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
        f.seek(6 + 2 + HEADER_LEN_SIZE)

        while i < HEADER_LEN:
            c = f.read(1)
            c = c.decode("utf-8")
            #print (c)
            descr += c
            i += 1
    return {
        'type': 'NUMPY',
        'version_major': major,
        'version_minor': minor,
        'header_length': HEADER_LEN + 6 + 2 + HEADER_LEN_SIZE,
        'description': eval(descr)
    }


# BASE READERS -----------------------------------------------------------------------------------------


class cilReaderInterface(VTKPythonAlgorithmBase):
    '''Base class with methods for setting and getting information about image data'''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)

        self._FileName = None
        self._IsFortran = False
        self._BigEndian = False
        self._FileHeaderLength = 0
        self._BytesPerElement = 1
        self._StoredArrayShape = None
        self._OutputVTKType = None
        self._NumpyTypeCode = None
        self._MetaImageTypeCode = None
        self._ElementSpacing = [1, 1, 1]
        self._Origin = (0., 0., 0.)
        self._IsAcquisitionData = False

    def SetFileName(self, value):
        ''' Set the file name or path from which to read the image data

        Parameters
        -----------
        value: (str)
            file name or path
        '''
        if not os.path.exists(value):
            raise ValueError('File does not exist!', value)

        if value != self.GetFileName():
            self._FileName = value
            self.Modified()

    def GetFileName(self):
        ''' get the file name or path from which the image data is read '''
        return self._FileName

    def FillInputPortInformation(self, port, info):
        '''This is a reader so no input'''
        return 1

    def FillOutputPortInformation(self, port, info):
        '''output should be of vtkImageData type'''
        info.Set(vtk.vtkDataObject.DATA_TYPE_NAME(), "vtkImageData")
        return 1

    def GetStoredArrayShape(self):
        ''' returns the shape of the data in self._FileName'''
        return self._StoredArrayShape

    def GetFileHeaderLength(self):
        ''' returns the length of the header in self._FileName, in bytes.
        If no header exists, the length is 0.'''
        return self._FileHeaderLength

    def GetBytesPerElement(self):
        ''' returns the number of bytes per element in self._FileName.
        The resampled data will also have this many bytes per element.'''
        return Converter.vtkType_to_bytes[self.GetOutputVTKType()]

    def GetBigEndian(self):
        ''' returns whether the data in self._FileName is big endian'''
        return self._BigEndian

    def GetIsFortran(self):
        ''' returns whether the data in self._FileName is saved in fortran order'''
        return self._IsFortran

    def GetOutputVTKType(self):
        ''' returns the VTK datatype the read data set will be returned in'''
        return self._OutputVTKType

    def SetStoredArrayShape(self, value):
        ''' Sets the shape of the dataset in self._FileName
        Currently only supports 3D datasets.

        Parameters
        -----------
        value: tuple
            shape of the dataset to be read from self._FileName,
            must be a tuple with length 3
        TODO: support 2D and 4D datasets too.'''
        if not isinstance(value, tuple):
            raise ValueError('Expected tuple, got {}'.format(type(value)))
        if len(value) != 3:
            raise ValueError('Expected tuple of length 3, got {}'.format(len(value)))
        self._StoredArrayShape = value

    def SetFileHeaderLength(self, value):
        ''' Sets the length of the header in self._FileName

        Parameters
        -----------
        value: int, default: 0
            the length of the header in bytes
        '''
        if not isinstance(value, int):
            raise ValueError('Expected int, got {}'.format(type(value)))
        self._FileHeaderLength = value

    def SetBigEndian(self, value):
        ''' Sets the endianness of the data in self._FileName

        Parameters
        -----------
        value: bool, default: False
            whether the dataset is big endian
        '''
        if not isinstance(value, bool):
            raise ValueError('Expected bool, got {}'.format(type(value)))
        self._BigEndian = value

    def SetIsFortran(self, value):
        ''' Sets whether the data in self._FileName is stored in fortran
        order.

        Parameters
        -----------
        value: bool, default: False
            whether the dataset is in fortran order
        '''
        if not isinstance(value, bool):
            raise ValueError('Expected bool, got {}'.format(type(value)))
        self._IsFortran = value

    def SetOutputVTKType(self, value):
        ''' Sets the VTK type the produced vtkImageData will be.

        Parameters
        ----------
        value:
            must be one of the values in this list:
            [vtk.VTK_SIGNED_CHAR,vtk.VTK_UNSIGNED_CHAR,
            vtk.VTK_SHORT, vtk.VTK_UNSIGNED_SHORT,
            vtk.VTK_INT, vtk.VTK_UNSIGNED_INT,
            vtk.VTK_FLOAT, vtk.VTK_DOUBLE]
            '''
        if value not in Converter.MetaImageType_to_vtkType.values():
            raise ValueError("Unexpected Type:  {}".format(value))
        self._OutputVTKType = value

    def GetMetaImageTypeCode(self):
        ''' Returns the typecode in meta image format, that could be written
        to a metaimage header.'''
        conversion_dict = {value: key for (key, value) in Converter.MetaImageType_to_vtkType.items()}
        return conversion_dict[self.GetOutputVTKType()]

    def GetElementSpacing(self):
        return self._ElementSpacing

    def SetElementSpacing(self, value):
        self._ElementSpacing = value

    def SetOrigin(self, value):
        ''' Sets the origin of the dataset in self._FileName.

        Parameters
        -----------
        value: tuple of length 3, default: (0, 0, 0)
            origin of the data set
        '''
        if not isinstance(value, tuple):
            raise ValueError('Expected a tuple. Got {}', type(value))

        if not value == self._Origin:
            self._Origin = value
            self.Modified()

    def GetOrigin(self):
        ''' Returns the origin of the dataset in self._FileName,
        as a tuple'''
        return self._Origin

    def SetIsAcquisitionData(self, value):
        '''
        Parameters
        -----------
        value: bool, default=False
            whether the dataset in self._FileName is acquisition data.
        '''
        self._IsAcquisitionData = value

    def GetIsAcquisitionData(self):
        '''
        returns whether the dataset in self._FileName is acquisition data.
        '''
        return self._IsAcquisitionData

    def GetTypeCodeName(self):
        ''' returns a human-readable string containing the data type'''
        conversion_dict = {value: key for (key, value) in Converter.dtype_name_to_vtkType.items()}
        return conversion_dict[self.GetOutputVTKType()]

    def SetTypeCodeName(self, value):
        if value not in Converter.dtype_name_to_vtkType.keys():
            raise ValueError("Unexpected Type: got {}. Please choose one of: {}".format(
                value, Converter.dtype_name_to_vtkType.keys()))
        self.SetOutputVTKType(Converter.dtype_name_to_vtkType[value])

    def ReadDataSetInfo(self):
        ''' Not implemented in the base class, but
        in the derived classes this should be a method
        which tries to read info about the dataset and
        will raise specific errors if inputs required for the 
        file type are not set.'''
        raise NotImplementedError("ReadDataSetInfo is not implemented in base class.")

    def GetOutput(self):
        return self.GetOutputDataObject(0)

    def _GetSliceLengthInFile(self):
        ''' Returns the length of each slice in
        the file, in bytes.'''
        nbytes = self.GetBytesPerElement()
        readshape = self.GetStoredArrayShape()
        is_fortran = self.GetIsFortran()

        if is_fortran:
            shape = list(readshape)
        else:
            shape = list(readshape)[::-1]

        # This is the length of each slice in the file:
        slice_length = shape[1] * shape[0] * nbytes

        return slice_length


class cilRawReaderInterface(cilReaderInterface):
    '''Baseclass with methods for reading information about raw files.'''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilRawReaderInterface, self).__init__()

    def ReadDataSetInfo(self):
        '''Tries to read info about dataset
        Will raise specific errors if inputs required for 
        reading raw image are not set.'''
        if self.GetStoredArrayShape() is None:
            raise Exception("StoredArrayShape must be set.")

        if self.GetOutputVTKType() is None:
            raise Exception("Typecode must be set.")


class cilNumpyReaderInterface(cilReaderInterface):
    ''' Baseclass with methods for reading information about numpy files'''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilNumpyReaderInterface, self).__init__()

    def ReadNpyHeader(self):
        '''extract info from the npy header'''
        descr = parseNpyHeader(self.GetFileName())
        # find the typecode of the data and the number of bytes per pixel
        for t in Converter.dtype_name_to_vtkType.keys():
            array_descr = descr['description']['descr'][1:]
            if array_descr == np.dtype(t).descr[0][1][1:]:
                typecode = t
                break

        big_endian = True if descr['description']['descr'][0] == '>' else False
        readshape = descr['description']['shape']
        is_fortran = descr['description']['fortran_order']
        file_header_length = descr['header_length']

        self.SetIsFortran(is_fortran)
        self.SetBigEndian(big_endian)
        self.SetFileHeaderLength(file_header_length)
        self.SetStoredArrayShape(readshape)
        self.SetTypeCodeName(typecode)
        self.Modified()

    def SetFileName(self, value):
        ''' Set the file name or path from which to read the image data
        
        Parameters
        -----------
        value: (str)
            file name or path
        '''
        if not os.path.exists(value):
            raise ValueError('File does not exist!', value)

        if value != self.GetFileName():
            self._FileName = value
            self.ReadNpyHeader()
            self.Modified()

    def ReadDataSetInfo(self):
        self.ReadNpyHeader()


class cilHDF5ReaderInterface(cilReaderInterface):
    ''' Baseclass with methods for setting and getting information about hdf5 files'''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilHDF5ReaderInterface, self).__init__()
        self._DatasetName = None

    def SetDatasetName(self, value):
        ''' Set the dataset name from which to read the image data

        Parameters
        -----------
        value: (str)
            dataset name
        '''
        if value != self._DatasetName:
            self._DatasetName = value
            if self.GetFileName() is not None:
                self.ReadDataSetInfo()

    def SetFileName(self, value):
        ''' Set the file name or path from which to read the image data

        Parameters
        -----------
        value: (str)
            file name or path
        '''
        if value != self.GetFileName():
            self._FileName = value
            if self.GetDatasetName() is not None:
                self.ReadDataSetInfo()

    def GetDatasetName(self):
        ''' Get the dataset name from which we read the image data'''
        return self._DatasetName

    def ReadDataSetInfo(self):
        ''' Get info about the HDF5 dataset, including shape and typecode,
        from the HDF5 file, and save as attributes of the class'''
        reader = HDF5Reader()
        reader.SetFileName(self.GetFileName())
        if self.GetDatasetName() is not None:
            reader.SetDatasetName(self.GetDatasetName())
        else:
            raise Exception("DataSetName must be set.")
        shape = reader.GetDimensions()
        # This is because the HDF5Reader already swaps the order:
        self.SetIsFortran(True)
        self.SetStoredArrayShape(shape)
        # get the datatype:
        typecode = str(np.dtype(reader.GetDataType()))
        self.SetOutputVTKType(Converter.dtype_name_to_vtkType[typecode])


class cilMetaImageReaderInterface(cilReaderInterface):
    ''' Baseclass with methods for setting and 
    getting information about metaimage files (.mha or .mhd)'''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilMetaImageReaderInterface, self).__init__()
        self._CompressedData = False
        self._ElementFile = None

    def ReadMetaImageHeader(self):
        ''' Read info from the metaimage file's header, 
        including endianness, origin, spacing, shape and typecode,
        and save as attributes of the class'''
        header_length = 0
        with open(self.GetFileName(), 'rb') as f:
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
                    # print(self.GetStoredArrayShape())
                elif 'ElementType' in line:
                    typecode = line.split('= ')[-1]
                    if typecode not in Converter.MetaImageType_to_vtkType.keys():
                        raise ValueError("Unexpected Type:  {}".format(typecode))
                    self.SetOutputVTKType(Converter.MetaImageType_to_vtkType[typecode])
                elif 'CompressedData' in line:
                    compressed = line.split('= ')[-1]
                    self.SetIsCompressedData(eval(compressed))
                    if self.GetIsCompressedData():
                        print("Cannot resample compressed image")
                        raise Exception("Cannot resample compressed image")
                elif 'HeaderSize' in line:
                    header_size = line.split('= ')[-1]
                    self.SetFileHeaderLength(int(header_size))
                elif 'ElementDataFile' in line:  # signifies end of header
                    element_data_file = line.split('= ')[-1]
                    if element_data_file != 'LOCAL':  # then we have an mhd file with data in another file
                        if not os.path.isabs(element_data_file):
                            file_path = os.path.dirname(self.GetFileName())
                            element_data_file = os.path.join(file_path, element_data_file)
                        # print("Filename: ", element_data_file)
                    else:
                        self.SetFileHeaderLength(header_length)
                    self.SetElementFile(element_data_file)
                    break

        self.SetIsFortran(True)
        self.Modified()

    def GetIsCompressedData(self):
        ''' Gets whether the image file is compressed.
        If True then we can't resample it.'''
        return self._CompressedData

    def SetIsCompressedData(self, value):
        ''' Sets whether the image file is compressed.
        If True then we can't resample it.

        Parameters
        -----------
        value: bool
            whether the file is compressed'''
        self._CompressedData = value

    def SetElementFile(self, value):
        self._ElementFile = value
        self.Modified()

    def GetElementFile(self):
        return self._ElementFile

    def ReadDataSetInfo(self):
        self.ReadMetaImageHeader()


class vortexTIFFImageReaderInterface(cilReaderInterface):
    ''' Baseclass with methods for setting and 
    getting information about tiff'''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(vortexTIFFImageReaderInterface, self).__init__()
        self._CompressedData = False

    def SetFileName(self, value):
        ''' Set the file name or path from which to read the image data

        Parameters
        -----------
        value: (str)
            file name or path
        '''
        if isinstance(value, (list, tuple)):
            for el in value:
                if not os.path.exists(el):
                    raise ValueError('File does not exist!', el)

        else:
            value = [value]
            return self.SetFileName(value)

        if value != self.GetFileName():
            self._FileName = value
            self.Modified()

    def GetIsCompressedData(self):
        ''' Gets whether the image file is compressed.
        If True then we can't resample it.'''
        return self._CompressedData

    def SetIsCompressedData(self, value):
        ''' Sets whether the image file is compressed.
        If True then we can't resample it.

        Parameters
        -----------
        value: bool
            whether the file is compressed'''
        self._CompressedData = value

    def ReadDataSetInfo(self):
        # this should set or do nothing
        self.SetIsFortran(True)
        self.SetBigEndian(False)
        # get one slice size
        reader = vtk.vtkTIFFReader()
        reader.SetFileName(self.GetFileName()[0])
        reader.Update()
        dimensions = reader.GetOutput().GetDimensions()
        zdim = len(self.GetFileName())
        if self.GetIsFortran():
            readshape = (dimensions[0], dimensions[1], zdim)
        else:
            readshape = (zdim, dimensions[1], dimensions[0])
        self.SetStoredArrayShape(readshape)

        self.SetOutputVTKType(reader.GetOutput().GetScalarType())

        self.Modified()


# ---------------------- RESAMPLE READERS -------------------------------------------------------------
class cilBaseResampleReader(cilReaderInterface):
    '''vtkAlgorithm to load and resample a file to an approximate memory footprint.
    This BaseClass provides the methods needed to resample a file, if the filename
    and dataset info has been set (these will be set in instances of derived classes)
    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilBaseResampleReader, self).__init__()

        self._TargetSize = 256**3
        self._SlicePerChunk = None
        self._TempDir = None
        self._ChunkReader = None

    def SetTargetSize(self, value):
        ''''
        Parameters
        -----------
        value (int), default=256*256*256:
            Total target size to downsample image to, in bytes.
            The resampler will aim for this approximate memory footprint.'''
        if not isinstance(value, int):
            raise ValueError('Expected an integer. Got {}', type(value))
        if not value == self.GetTargetSize():
            self._TargetSize = value
            self.Modified()

    def GetTargetSize(self):
        ''' Get the total target size to downsample image to, in bytes.'''
        return self._TargetSize

    def _GetInternalChunkReader(self):
        ''' Returns a reader which can be used to read each chunk.
        The reader is always going to read the header file: header.mhd, and
        the data is always being read from chunk.raw a.k.a. self._ChunkFileName.
        This method creates these files, with the header file containing the information
        for a dataset which is equal to the size of a chunk needed in the downsampling.
        
        We have to make a new metaimage header so that the vtk.vtkMetaImageReader
        knows the extent it needs to read when we read a chunk.
        
        TODO: In future we need to use the vtk.vtkImageReader2 to replace this
        and remove the need for re-writing out chunks.
        '''
        raise NotImplemented

    def UpdateChunkToRead(self, start_slice):
        '''Read the next chunk from the image file,
        and write out to self._ChunkFileName
        It is self._ChunkFileName that is being read by the resampler
        so essentially this method is updating which chunk of data the 
        resampler will receive.
        '''
        raise NotImplemented

    def _SetNumSlicesPerChunk(self, value):
        '''
        Parameters
        -----------
        value: (int)
            number of slices in the z direction we are resampling together'''
        self._SlicePerChunk = value

    def _GetNumSlicesPerChunk(self):
        '''get number of slices in the z direction we are resampling together'''
        return self._SlicePerChunk

    def _GetTempDir(self):
        '''get the temporary directory where we save the chunks as they are being read'''
        return self._TempDir

    def _SetTempDir(self, folder):
        '''set the temporary directory where we save the chunks as they are being read'''
        self._TempDir = folder

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

            total_size = shape[0] * shape[1] * shape[2] * self.GetBytesPerElement()

            max_size = self.GetTargetSize()

            if total_size < max_size:  # in this case we don't need to resample
                # set the chunk size to equal the total extent of the dataset:
                self._SetNumSlicesPerChunk(shape[2])
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
                    xy_axes_magnification = np.power(max_size / total_size, 1 / 3)
                    num_slices_per_chunk = int(
                        1 / xy_axes_magnification)  # number of slices in the z direction we are resampling together.
                else:
                    # If we have acquisition data we don't want to resample in the z
                    # direction because then we would be averaging projections together,
                    # so we have one slice per chunk
                    num_slices_per_chunk = 1  # number of slices in the z direction we are resampling together.
                    xy_axes_magnification = np.power(max_size / total_size, 1 / 2)

                # Each chunk will be the z slices that we will resample together to form one new slice.
                # Each chunk will contain num_slices_per_chunk number of slices.
                self._SetNumSlicesPerChunk(num_slices_per_chunk)

                # print("Slice per chunk: ", num_slices_per_chunk)

                # indices of the first slice per chunk
                # we will read in num_slices_per_chunk slices at a time
                start_sliceno_in_chunks = [i for i in range(0, shape[2], num_slices_per_chunk)]

                num_chunks = len(start_sliceno_in_chunks)  # the number of chunks we will read in total

                # in the case of acquisition data this will be 1 as num_chunks=shape[2]:
                z_axis_magnification = num_chunks / (shape[2])

                target_image_shape = (int(xy_axes_magnification * shape[0]), int(xy_axes_magnification * shape[1]),
                                      num_chunks)

                resampler = vtk.vtkImageReslice()

                element_spacing = self.GetElementSpacing()

                resampler.SetOutputSpacing(element_spacing[0] / xy_axes_magnification,
                                           element_spacing[1] / xy_axes_magnification,
                                           element_spacing[2] / z_axis_magnification)
                # resampled data
                resampled_image = outData

                resampled_image.SetExtent(0, target_image_shape[0] - 1, 0, target_image_shape[1] - 1, 0,
                                          target_image_shape[2] - 1)

                resampled_image.SetSpacing(element_spacing[0] / xy_axes_magnification,
                                           element_spacing[1] / xy_axes_magnification,
                                           element_spacing[2] / z_axis_magnification)

                new_spacing = [
                    element_spacing[0] / xy_axes_magnification, element_spacing[1] / xy_axes_magnification,
                    element_spacing[2] / z_axis_magnification
                ]

                original_origin = self.GetOrigin()
                '''The new origin is based on where we need to position each slice in the world
                If we have an image which is downsampled by 5 times, 
                slices 0-4 are downsampled to a single slice and the image spacing is 5.
                Slice 0 in image coordinates corresponds to slices 0-4 in the actual image.
                The clipping planes will need to include points ranging from -0.5 to 4.49.
                Therefore the slice needs to be centred half way through this range: at 2.
                Because world coordinates = image coords * spacing + origin,
                we need the origin to be 2 for this image.

                In general, the origin must be at (image_spacing-1)/2 plus the original
                position of the image's origin:'''
                new_origin = tuple([(s - 1) / 2 + original_origin[i] for i, s in enumerate(new_spacing)])

                resampled_image.SetOrigin(new_origin)

                resampled_image.AllocateScalars(self.GetOutputVTKType(), 1)

                reader = self._GetInternalChunkReader()

                resampler.SetInputData(reader.GetOutput())

                # process each chunk:
                for i, start_sliceno in enumerate(start_sliceno_in_chunks):
                    self.UpdateChunkToRead(start_sliceno)
                    reader.Modified()
                    reader.Update()
                    # print(i, reader.GetOutput().GetScalarComponentAsDouble(0,0,0,0))

                    # change the extent of the resampled image
                    extent = (0, target_image_shape[0] - 1, 0, target_image_shape[1] - 1, i, i)

                    resampler.SetOutputExtent(extent)
                    resampler.Update()
                    # print(i, resampler.GetOutput().GetScalarComponentAsDouble(0,0,i,0))

                    ################# vtk way ####################
                    resampled_image.CopyAndCastFrom(resampler.GetOutput(), extent)
                    self.UpdateProgress(i / num_chunks)
        except Exception as e:
            raise Exception(e)

        finally:
            tmpdir = self._GetTempDir()
            if tmpdir is not None:
                if os.path.exists(tmpdir):
                    shutil.rmtree(self._GetTempDir())

        return 1


class cilBaseBinaryBlobResampleReader(cilBaseResampleReader):
    '''vtkAlgorithm to load and resample a file to an approximate memory footprint.
    This BaseClass provides the methods needed to resample a file, if the filename
    and dataset info has been set (these will be set in instances of derived classes)
    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilBaseBinaryBlobResampleReader, self).__init__()

        self._TargetSize = 256**3
        self._SlicePerChunk = None
        self._TempDir = None
        self._ChunkReader = None

    def _GetInternalChunkReader(self):
        ''' Returns a reader which can be used to read each chunk.
        The reader is always going to read the header file: header.mhd, and
        the data is always being read from chunk.raw a.k.a. self._ChunkFileName.
        This method creates these files, with the header file containing the information
        for a dataset which is equal to the size of a chunk needed in the downsampling.
        
        We have to make a new metaimage header so that the vtk.vtkMetaImageReader
        knows the extent it needs to read when we read a chunk.
        
        TODO: In future we need to use the vtk.vtkImageReader2 to replace this
        and remove the need for re-writing out chunks.
        '''
        tmpdir = tempfile.mkdtemp()
        self._SetTempDir(tmpdir)
        header_filename = os.path.join(tmpdir, "header.mhd")
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(header_filename)

        chunk_file_name = os.path.join(tmpdir, "chunk.raw")
        self._ChunkFileName = chunk_file_name

        readshape = self.GetStoredArrayShape()
        is_fortran = self.GetIsFortran()

        if is_fortran:
            shape = list(readshape)
        else:
            shape = list(readshape)[::-1]

        chunk_shape = shape.copy()
        if self._GetNumSlicesPerChunk() is not None:
            num_slices_per_chunk = self._GetNumSlicesPerChunk()
        else:
            num_slices_per_chunk = shape[2]
        chunk_shape[2] = num_slices_per_chunk

        cilNumpyMETAImageWriter.WriteMETAImageHeader(chunk_file_name,
                                                     header_filename,
                                                     self.GetMetaImageTypeCode(),
                                                     self.GetBigEndian(),
                                                     0,
                                                     tuple(chunk_shape),
                                                     spacing=tuple(self.GetElementSpacing()),
                                                     origin=self.GetOrigin())
        self._ChunkReader = reader
        return reader

    def UpdateChunkToRead(self, start_slice):
        '''Read the next chunk from the image file,
        and write out to self._ChunkFileName
        It is self._ChunkFileName that is being read by the resampler
        so essentially this method is updating which chunk of data the 
        resampler will receive.
        '''

        # This is the length of the chunk we will read from the file in bytes:
        chunk_length = self._GetSliceLengthInFile() * self._GetNumSlicesPerChunk()

        with open(self.GetFileName(), "rb") as image_file_object:
            if start_slice < 0:
                raise ValueError('{} ERROR: Start slice cannot be negative.'.format(self.__class__.__name__))
            chunk_location = self.GetFileHeaderLength() + start_slice * self._GetSliceLengthInFile()
            with open(self._ChunkFileName, "wb") as chunk_file_object:
                image_file_object.seek(chunk_location)
                chunk = image_file_object.read(chunk_length)
                chunk_file_object.write(chunk)


class cilRawResampleReader(cilBaseBinaryBlobResampleReader, cilRawReaderInterface):
    '''vtkAlgorithm to load and resample a raw file to an approximate memory footprint

    Example
    -------
    This example reads a raw dataset from the file: data.raw and downsamples
    it to an approx. size of 1GB:

    reader = cilRawResampleReader()
    reader.SetFileName('data.raw')
    reader.SetTargetSize(1024*1024*1024)
    reader.SetBigEndian(False)
    reader.SetIsFortran(False)
    reader.SetTypeCodeName('uint16')
    reader.SetStoredArrayShape((1520, 1257, 1260))
    reader.Update()
    image = reader.GetOutput()
    
    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilRawResampleReader, self).__init__()


class cilNumpyResampleReader(cilNumpyReaderInterface, cilBaseBinaryBlobResampleReader):
    '''vtkAlgorithm to load and resample a numpy file to an approximate memory footprint
    
    Example
    -------
    This example reads a numpy dataset from the file: data.npy and downsamples
    it to an approx. size of 1GB:

    reader = cilNumpyResampleReader()
    reader.SetFileName('data.npy')
    reader.SetTargetSize(1024*1024*1024)
    reader.Update()
    image = reader.GetOutput()
    
    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilNumpyResampleReader, self).__init__()


class cilHDF5ResampleReader(cilBaseResampleReader, cilHDF5ReaderInterface):
    '''vtkAlgorithm to load and resample a HDF5 file to an approximate memory footprint

    Example
    -------
    This example reads a HDF5 image from the 'entry1/tomo_entry/data/data'
    dataset of the file: data.nxs and downsamples it to an approx. size of 1GB:

    reader = cilHDF5ResampleReader()
    reader.SetFileName('data.nxs')
    reader.SetDatasetName('entry1/tomo_entry/data/data')
    reader.SetTargetSize(1024*1024*1024)
    reader.Update()
    image = reader.GetOutput()
    
    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilHDF5ResampleReader, self).__init__()

    def _GetInternalChunkReader(self):
        '''returns a reader which will only read a specific chunk of the data.
        This is a chunk which will get resampled into a single slice.'''
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
        # Set default extent to full extent:
        cropped_reader.SetUpdateExtent((0, -1, 0, -1, 0, -1))
        self._ChunkReader = cropped_reader
        return cropped_reader

    def UpdateChunkToRead(self, start_slice):
        ''' updates the chunk reader to read the next chunk starting at extent
        start_slice in the z direction'''
        num_slices_per_chunk = self._GetNumSlicesPerChunk()
        end_slice = start_slice + num_slices_per_chunk - 1
        end_z_value = self.GetStoredArrayShape()[2] - 1
        if end_slice > end_z_value:
            end_slice = end_z_value
        if start_slice < 0:
            raise ValueError('{} ERROR: Start slice cannot be negative.'.format(self.__class__.__name__))
        dims = self.GetStoredArrayShape()
        self._ChunkReader.SetUpdateExtent((0, dims[0] - 1, 0, dims[1] - 1, start_slice, end_slice))


class cilMetaImageResampleReader(cilBaseBinaryBlobResampleReader, cilMetaImageReaderInterface):
    '''vtkAlgorithm to load and resample a metaimage file to an approximate memory footprint
    
    Example
    --------
    This example reads a metaimage dataset from the file: data.mha and downsamples
    it to an approx. size of 1GB:

    reader = cilMetaImageResampleReader()
    reader.SetFileName('data.mha')
    reader.SetTargetSize(1024*1024*1024)
    reader.Update()
    image = reader.GetOutput()
    
    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilMetaImageResampleReader, self).__init__()

    def UpdateChunkToRead(self, start_slice):
        '''Read the next chunk from the image file,
        and write out to self._ChunkFileName
        It is self._ChunkFileName that is being read by the resampler
        so essentially this method is updating which chunk of data the 
        resampler will receive.
        '''

        # This is the length of the chunk we will read from the file in bytes:
        chunk_length = self._GetSliceLengthInFile() * self._GetNumSlicesPerChunk()

        data_fname = self.GetElementFile()
        if data_fname == 'LOCAL':
            data_fname = self.GetFileName()

        with open(data_fname, "rb") as image_file_object:
            if start_slice < 0:
                raise ValueError('{} ERROR: Start slice cannot be negative.'.format(self.__class__.__name__))
            chunk_location = self.GetFileHeaderLength() + start_slice * self._GetSliceLengthInFile()
            with open(self._ChunkFileName, "wb") as chunk_file_object:
                image_file_object.seek(chunk_location)
                chunk = image_file_object.read(chunk_length)
                chunk_file_object.write(chunk)


class vortexTIFFResampleReader(cilBaseResampleReader, vortexTIFFImageReaderInterface):

    def _GetInternalChunkReader(self):
        '''returns a reader which will only read a specific chunk of the data.
        This is a chunk which will get resampled into a single slice.'''
        reader = vtk.vtkTIFFReader()
        self._ChunkReader = reader
        return reader

    def UpdateChunkToRead(self, start_slice):
        ''' updates the chunk reader to read the next chunk starting at extent
        start_slice in the z direction'''
        num_slices_per_chunk = self._GetNumSlicesPerChunk()
        end_slice = start_slice + num_slices_per_chunk - 1
        end_z_value = self.GetStoredArrayShape()[2] - 1
        if end_slice > end_z_value:
            end_slice = end_z_value
        if start_slice < 0:
            raise ValueError('{} ERROR: Start slice cannot be negative.'.format(self.__class__.__name__))
        dims = self.GetStoredArrayShape()

        fnames = self.GetFileName()
        chunk = vtk.vtkStringArray()
        for i in range(start_slice, end_slice + 1):
            chunk.InsertNextValue(fnames[i])
        self._ChunkReader.SetFileNames(chunk)


# CROPPED READERS -----------------------------------------------------------------------------------


class cilBaseCroppedReader(cilReaderInterface):
    '''vtkAlgorithm to crop in the z direction
    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilBaseCroppedReader, self).__init__()
        self._TargetZExtent = (0, 0)

    def SetTargetZExtent(self, value):
        ''' 
        Set the target extent to crop to on the z axis.
        
        Parameters
        -----------
        value: list of len 2
            the extent on the z axis to crop the dataset to
        '''
        if not isinstance(value, tuple):
            raise ValueError('Expected a tuple. Got {}', type(value))

        if not value == self.GetTargetZExtent():
            self._TargetZExtent = value
            self.Modified()

    def GetTargetZExtent(self):
        ''' 
        Get the target extent to crop to on the z axis.
        '''
        return self._TargetZExtent

    def RequestData(self, request, inInfo, outInfo):
        outData = vtk.vtkImageData.GetData(outInfo)

        self.ReadDataSetInfo()

        # get basic info
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

        slice_length = self._GetSliceLengthInFile()

        try:
            if self.GetTargetZExtent()[1] >= shape[2] and self.GetTargetZExtent()[0] <= 0:
                # in this case we don't need to crop, so we read the whole dataset
                # print("Don't crop")

                chunk_file_name = os.path.join(tmpdir, "chunk.raw")

                # Creates a metaimageheader which will be used to read a file containing the
                # data - chunk_file_name which we will fill below.

                cilNumpyMETAImageWriter.WriteMETAImageHeader(chunk_file_name,
                                                             header_filename,
                                                             self.GetMetaImageTypeCode(),
                                                             big_endian,
                                                             0,
                                                             tuple(shape),
                                                             spacing=tuple(self.GetElementSpacing()),
                                                             origin=self.GetOrigin())

                image_file = self.GetFileName()
                # Writes the entire dataset to chunk_file_name
                with open(image_file, "rb") as image_file_object:
                    end_slice = shape[2]
                    chunk_location = file_header_length
                    with open(chunk_file_name, "wb") as chunk_file_object:
                        image_file_object.seek(chunk_location)
                        chunk_length = slice_length * end_slice
                        chunk = image_file_object.read(chunk_length)
                        chunk_file_object.write(chunk)

                reader.Modified()
                reader.Update()
                # print(reader.GetOutput().GetScalarComponentAsDouble(0, 0, 0, 0))
                outData.ShallowCopy(reader.GetOutput())

                return 1

            # In the case we do need to crop: ---------------------------------------------

            shape[2] = self.GetTargetZExtent()[1] - self.GetTargetZExtent()[0] + 1

            chunk_file_name = os.path.join(tmpdir, "chunk.raw")

            # Creates a metaimageheader which will be used to read a file just containing the cropped
            # data - chunk_file_name which we will fill below.
            cilNumpyMETAImageWriter.WriteMETAImageHeader(chunk_file_name,
                                                         header_filename,
                                                         self.GetMetaImageTypeCode(),
                                                         big_endian,
                                                         0,
                                                         tuple(shape),
                                                         spacing=tuple(self.GetElementSpacing()),
                                                         origin=self.GetOrigin())
            image_file = self.GetFileName()
            chunk_location = file_header_length + \
                (self.GetTargetZExtent()[0]) * slice_length

            # Reads the data as a single chunk.
            # Copies the chunk from the original file to chunk_file_name:
            with open(chunk_file_name, "wb") as chunk_file_object:
                with open(image_file, "rb") as image_file_object:
                    image_file_object.seek(chunk_location)
                    chunk_length = (self.GetTargetZExtent()[1] - self.GetTargetZExtent()[0] + 1) * slice_length
                    chunk = image_file_object.read(chunk_length)
                    chunk_file_object.write(chunk)

            reader.Modified()
            reader.Update()

            # Once we have read the data, update the extent to reflect where
            # we have cut the cropped dataset out of the original image
            Data = vtk.vtkImageData()
            extent = (0, shape[0] - 1, 0, shape[1] - 1, self.GetTargetZExtent()[0], self.GetTargetZExtent()[1])
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
            raise Exception(e)
        finally:
            if os.path.exists(tmpdir):
                shutil.rmtree(tmpdir)
        return 1


class cilRawCroppedReader(cilBaseCroppedReader, cilRawReaderInterface):
    '''vtkAlgorithm to load and crop a raw file

    Example
    --------
    This example reads a raw image from the file: data.raw and crops it
    to exetnt [1, 3] on the z axis:

    reader = cilRawCroppedReader()
    reader.SetFileName('data.raw')
    reader.SetTargetZExtent((1, 3))
    reader.SetBigEndian(False)
    reader.SetIsFortran(False)
    reader.SetTypeCodeName("uint8")
    reader.SetStoredArrayShape((50,100,60))
    reader.Update()
    image = reader.GetOutput()

    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilRawCroppedReader, self).__init__()


class cilNumpyCroppedReader(cilBaseCroppedReader, cilNumpyReaderInterface):
    '''vtkAlgorithm to load and crop a numpy file

    Example
    --------
    This example reads a raw image from the file: data.npy and crops it
    to extent [1, 3] on the z axis:

    reader = cilNumpyCroppedReader()
    reader.SetFileName('data.npy')
    reader.SetTargetZExtent((1, 3))
    reader.Update()
    image = reader.GetOutput()
    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilNumpyCroppedReader, self).__init__()


class cilMetaImageCroppedReader(cilBaseCroppedReader, cilMetaImageReaderInterface):
    '''vtkAlgorithm to load and resample a metaimage file to an approximate memory footprint

    Example
    -------
    This example reads a raw image from the file: data.mha and crops it
    to extent [1, 3] on the z axis:

    reader = cilMetaImageCroppedReader()
    reader.SetFileName('data.mha')
    reader.SetTargetZExtent((1, 3))
    reader.Update()
    image = reader.GetOutput()
    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilMetaImageCroppedReader, self).__init__()


class cilHDF5CroppedReader(cilBaseCroppedReader, cilHDF5ReaderInterface):
    '''vtkAlgorithm to load and crop a hdf5 file

    Example
    -------
    This example reads a HDF5 image from the
    'entry1/tomo_entry/data/data' dataset of the
    file: data.nxs and crops it to extent (0, 2, 3, 5, 1, 2):

    reader = cilHDF5CroppedReader()
    reader.SetFileName('data.nxs')
    reader.SetDatasetName('entry1/tomo_entry/data/data')
    reader.SetTargetExtent((0, 2, 3, 5, 1, 2))
    reader.Update()
    image = reader.GetOutput()
    
    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilHDF5CroppedReader, self).__init__()
        self._TargetExtent = None

    def SetTargetExtent(self, value):
        ''' 
        Set the target extent to crop to. Unlike other cropped readers,
        the HDF5CroppedReader can crop in all dimensions

        Parameters
        -----------
        value: list of len 5
            the extent to crop the dataset to
        '''
        self._TargetExtent = value

    def GetTargetExtent(self):
        ''' Returns the target extent to crop to. Unlike other cropped readers,
        the HDF5CroppedReader can crop in all dimensions'''
        return self._TargetExtent

    def RequestData(self, request, inInfo, outInfo):
        outData = vtk.vtkImageData.GetData(outInfo)

        full_reader = HDF5Reader()
        full_reader.SetFileName(self.GetFileName())
        full_reader.SetDatasetName(self.GetDatasetName())
        reader = HDF5SubsetReader()
        reader.SetInputConnection(full_reader.GetOutputPort())
        # Either the TargetExtent or TargetZExtent should have been set.
        # We prioritise the TargetExtent
        if self.GetTargetExtent() is None:
            extent = [0, -1, 0, -1, self.GetTargetZExtent[0], self.GetTargetZExtent[1]]
        else:
            extent = self.GetTargetExtent()
        reader.SetUpdateExtent(extent)
        reader.Update()
        read_data = reader.GetOutput()
        outData.ShallowCopy(read_data)

        return 1


class vortexTIFFCroppedReader(cilBaseCroppedReader, vortexTIFFImageReaderInterface):
    '''vtkAlgorithm to load and crop a TIFF files

    Example
    -------
    This example reads a HDF5 image from the
    'entry1/tomo_entry/data/data' dataset of the
    file: data.nxs and crops it to extent (0, 2, 3, 5, 1, 2):

    reader = cilHDF5CroppedReader()
    reader.SetFileName('data.nxs')
    reader.SetDatasetName('entry1/tomo_entry/data/data')
    reader.SetTargetExtent((0, 2, 3, 5, 1, 2))
    reader.Update()
    image = reader.GetOutput()
    
    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(vortexTIFFCroppedReader, self).__init__()
        self._TargetExtent = None

    def SetTargetExtent(self, value):
        ''' 
        Set the target extent to crop to. Unlike other cropped readers,
        the HDF5CroppedReader can crop in all dimensions

        Parameters
        -----------
        value: list of len 5
            the extent to crop the dataset to
        '''
        self._TargetExtent = value

    def GetTargetExtent(self):
        ''' Returns the target extent to crop to. Unlike other cropped readers,
        the HDF5CroppedReader can crop in all dimensions'''
        return self._TargetExtent

    def RequestData(self, request, inInfo, outInfo):
        outData = vtk.vtkImageData.GetData(outInfo)

        self.ReadDataSetInfo()

        # get basic info
        big_endian = self.GetBigEndian()
        readshape = self.GetStoredArrayShape()
        file_header_length = self.GetFileHeaderLength()
        is_fortran = self.GetIsFortran()

        if is_fortran:
            shape = list(readshape)
        else:
            shape = list(readshape)[::-1]

        tmpdir = tempfile.mkdtemp()
        reader = vtk.vtkTIFFReader()
        sa = vtk.vtkStringArray()

        # Either the TargetExtent or TargetZExtent should have been set.
        # We prioritise the TargetExtent
        if self.GetTargetExtent() is None:
            extent = [0, -1, 0, -1, self.GetTargetZExtent()[0], self.GetTargetZExtent()[1]]
        else:
            extent = self.GetTargetExtent()

        # crop on Z
        if extent[5] >= shape[2] and extent[4] <= 0:
            # in this case we don't need to crop, so we read the whole dataset
            # print("Don't crop")
            for el in self.GetFileName():
                sa.InsertNextValue(el)
            reader.SetFileNames(sa)        
            reader.Update()
            outData.ShallowCopy(reader.GetOutput())

            return 1

        # In the case we do need to crop: ---------------------------------------------

        shape[2] = self.GetTargetZExtent()[1] - self.GetTargetZExtent()[0] + 1

        image_file = self.GetFileName()[extent[4]:extent[5]+1]
        for el in image_file:
            sa.InsertNextValue(el)
        reader.SetFileNames(sa) 
        reader.Update()

        # Once we have read the data, update the extent to reflect where
        # we have cut the cropped dataset out of the original image
        
        Data = vtk.vtkImageData()
        extent = (0, shape[0] - 1, 0, shape[1] - 1, self.GetTargetZExtent()[0], self.GetTargetZExtent()[1])
        Data.SetExtent(extent)
        Data.SetSpacing(self.GetElementSpacing())
        Data.SetOrigin(self.GetOrigin())
        Data.AllocateScalars(self.GetOutputVTKType(), 1)

        read_data = reader.GetOutput()
        read_data.SetExtent(extent)

        Data.CopyAndCastFrom(read_data, extent)
        outData.ShallowCopy(Data)

        return 1


# ------------ RESAMPLE FROM MEMORY: ------------------------------------------------------------------------------


class vtkImageResampler(VTKPythonAlgorithmBase):
    '''vtkAlgorithm resample vtkImageData to an approximate memory footprint.
    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
                                        nInputPorts=1,
                                        inputType="vtkImageData",
                                        nOutputPorts=1,
                                        outputType="vtkImageData")

        self._TargetSize = 256**3
        self._IsAcquisitionData = False

    def SetIsAcquisitionData(self, value):
        '''
        Parameters
        -----------
        value: bool, default=False
            whether the dataset is acquisition data.
        '''
        self._IsAcquisitionData = value
        self.Modified()

    def GetIsAcquisitionData(self):
        '''
        returns whether the dataset is acquisition data.
        '''
        return self._IsAcquisitionData

    def SetTargetSize(self, value):
        ''''
        Parameters
        -----------
        value (int), default=256*256*256:
            Total target size to downsample image to, in bytes.
            The resampler will aim for this approximate memory footprint.'''
        if not isinstance(value, int):
            raise ValueError('Expected an integer. Got {}', type(value))
        if not value == self.GetTargetSize():
            self._TargetSize = value
            self.Modified()

    def GetTargetSize(self):
        ''' Get the total target size to downsample image to, in bytes.'''
        return self._TargetSize

    def GetBytesPerElement(self):
        ''' Get number of bytes per element'''
        if hasattr(self, '_BytesPerElement'):
            return self._BytesPerElement

    def GetOutput(self):
        return self.GetOutputDataObject(0)

    def ReadDataSetInfo(self, inData):
        self._ElementSpacing = inData.GetSpacing()
        self._Origin = inData.GetOrigin()
        self._Extent = inData.GetExtent()
        self._StoredArrayShape = (self._Extent[1] + 1, (self._Extent[3] + 1), (self._Extent[5] + 1))
        self._BytesPerElement = Converter.vtkType_to_bytes[inData.GetScalarType()]

    def GetElementSpacing(self):
        ''' Returns the spacing of the input dataset as a tuple'''
        return self._ElementSpacing

    def GetOrigin(self):
        ''' Returns the origin of the input dataset as a tuple'''
        return self._Origin

    def GetExtent(self):
        ''' Returns the extent of the input dataset as a tuple'''
        return self._Extent

    def GetStoredArrayShape(self):
        ''' Returns the shape of the input dataset as a tuple'''
        return self._StoredArrayShape

    def RequestData(self, request, inInfo, outInfo):
        inData = vtk.vtkImageData.GetData(inInfo[0])
        outData = vtk.vtkImageData.GetData(outInfo)

        self.ReadDataSetInfo(inData)

        extent = self.GetExtent()
        shape = self.GetStoredArrayShape()

        total_size = shape[0] * shape[1] * shape[2] * self.GetBytesPerElement()

        max_size = self.GetTargetSize()

        if total_size < max_size:
            # in this case we don't need to resample
            outData.ShallowCopy(inData)

        else:

            # scaling is going to be similar in every axis
            # (xy the same, z possibly different)
            if not self.GetIsAcquisitionData():
                xy_axes_magnification = np.power(max_size / total_size, 1 / 3)
                num_slices_per_chunk = int(
                    1 / xy_axes_magnification)  # number of slices in the z direction we are resampling together.
            else:
                # If we have acquisition data we don't want to resample in the z
                # direction because then we would be averaging projections together,
                # so we have one slice per chunk
                num_slices_per_chunk = 1  # number of slices in the z direction we are resampling together.
                xy_axes_magnification = np.power(max_size / total_size, 1 / 2)

            # Each chunk will be the z slices that we will resample together to form one new slice.
            # Each chunk will contain num_slices_per_chunk number of slices.

            # indices of the first slice per chunk
            start_sliceno_in_chunks = [i for i in range(0, shape[2], num_slices_per_chunk)]

            num_chunks = len(start_sliceno_in_chunks)  # the number of chunks we will read in total

            # in the case of acquisition data this will be 1 as num_chunks=shape[2]:
            z_axis_magnification = num_chunks / (shape[2])

            target_image_shape = (int(xy_axes_magnification * shape[0]), int(xy_axes_magnification * shape[1]),
                                  num_chunks)

            resampler = vtk.vtkImageReslice()

            element_spacing = self.GetElementSpacing()

            resampler.SetOutputSpacing(element_spacing[0] / xy_axes_magnification,
                                       element_spacing[1] / xy_axes_magnification,
                                       element_spacing[2] / z_axis_magnification)

            resampler.SetInputData(inData)

            # change the extent of the resampled image
            extent = (0, target_image_shape[0] - 1, 0, target_image_shape[1] - 1, 0, target_image_shape[2] - 1)

            resampler.SetOutputExtent(extent)
            resampler.Update()

            # resampled data:
            resampled_image = resampler.GetOutput()
            new_spacing = [
                element_spacing[0] / xy_axes_magnification, element_spacing[1] / xy_axes_magnification,
                element_spacing[2] / z_axis_magnification
            ]

            original_origin = self.GetOrigin()
            '''The new origin is based on where we need to position each slice in the world
            If we have an image which is downsampled by 5 times, 
            slices 0-4 are downsampled to a single slice and the image spacing is 5.
            Slice 0 in image coordinates corresponds to slices 0-4 in the actual image.
            The clipping planes will need to include points ranging from -0.5 to 4.49.
            Therefore the slice needs to be centred half way through this range: at 2.
            Because world coordinates = image coords * spacing + origin,
            we need the origin to be 2 for this image.

            In general, the origin must be at (image_spacing-1)/2 plus the original
            position of the image's origin:'''
            new_origin = tuple([(s - 1) / 2 + original_origin[i] for i, s in enumerate(new_spacing)])
            resampled_image.SetOrigin(new_origin)
            resampled_image.SetSpacing(element_spacing[0] / xy_axes_magnification,
                                       element_spacing[1] / xy_axes_magnification,
                                       element_spacing[2] / z_axis_magnification)

            outData.ShallowCopy(resampled_image)

        return 1


if __name__ == '__main__':
    '''this represent a good base to perform a test for the numpy-metaimage writer'''
    dimX = 128
    dimY = 64
    dimZ = 32
    # a = numpy.zeros((dimX,dimY,dimZ), dtype=numpy.uint16)
    a = numpy.random.randint(0, size=(dimX, dimY, dimZ), high=127, dtype=numpy.uint16)
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
    hdrdescr = parseNpyHeader(arfn + '.npy')

    #a = numpy.load(arfn+'.npy')

    #import matplotlib.pyplot as plt
    # plt.imshow(a[10,:,:])
    # plt.show()

    reader = vtk.vtkMetaImageReader()
    reader.SetFileName(arfn + '.mhd')
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
                    v2 = numpy.uint8(reader.GetOutput().GetScalarComponentAsFloat(x, y, z, 0))
                    # print ("value check {} {} {},".format((x,y,z) ,v1,v2))
                    is_same = v1 == v2
                    if not is_same:
                        raise ValueError('arrays do not match', v1, v2, x, y, z)
        print('YEEE array match!')
