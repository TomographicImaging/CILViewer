import imghdr
import os
import shutil
import sys
import time
from functools import partial

import numpy
import vtk
from ccpi.viewer.utils import Converter
from ccpi.viewer.utils.conversion import (cilBaseCroppedReader,
                                          cilBaseResampleReader,
                                          cilMetaImageCroppedReader,
                                          cilMetaImageResampleReader,
                                          cilNumpyCroppedReader,
                                          cilNumpyResampleReader)

import glob

import logging




# Currently doesn't support both cropping and resampling
# If set both to true then it resamples and doesn't crop


# TODO: look at getting progress from readers


class ImageReader(object):

    def __init__(self, **kwargs):
        '''
        Constructor
        
        Parameters
        ----------
        file_name: os.path or string, default None
            file name to read
        resample: bool, default False
            whether to resample
        crop: bool, default False
            whether to crop
        target_size: int
            target size after downsampling (bytes)
        target_z_extent: list [,]
            desired extent after cropping on z axis
        raw_image_attrs: dict {'dimensions': 2D or 3D array, 'is_fortran':bool, 'is_big_endian':bool
            'type_code':info_var['typcode']}, default None
                    
        '''
        file_name = kwargs.get('file_name', None)
        resample = kwargs.get('resample', True)
        target_size = kwargs.get('target_size', 512**3)
        crop = kwargs.get('crop', False)
        target_z_extent = kwargs.get('target_z_extent', None)
        raw_image_attrs = kwargs.get('raw_image_attrs', None)

        self.set_up(file_name, resample, target_size, crop, target_z_extent, raw_image_attrs)

    def set_up(self,  file_name = None, resample=True, target_size=512**3, crop=False, target_z_extent=None, raw_image_attrs=None):

        if file_name == None:
            raise Exception('Path to file is required.')

        if not (os.path.isfile(file_name) or os.path.isdir(file_name)):
            raise Exception('Path\n {}\n does not exist.'.format(file_name))

        self.file_name = file_name
        self.resample = resample
        self.target_size = target_size
        self.crop = crop
        self.target_z_extent = target_z_extent
        self.image_attrs = {} # TODO: change how this works

        self._set_up_logger("ImageReader.log")
            
    def read(self, *args, **kwargs):
        ''' reads self.file_name
            returns vtkImageData'''
        # identifies file type
        # uses appropriate reader based on file type and cropping or resampling

        progress_callback = kwargs.get('progress_callback')
        print("The progress callback: ", progress_callback)

        if os.path.isfile(self.file_name):
            file_extension = os.path.splitext(self.file_name)[1]

        else:
            # TODO: test this
            image_files = glob.glob(os.path.join(self.file_name, '*'))
            for image in image_files:
                file_extension = imghdr.what(image)
                if file_extension != 'tiff':
                    raise Exception('When reading multiple files, all files must TIFF formatted.')

        if file_extension in ['.mha', '.mhd']:
            return self._read_meta_image(progress_callback)

        elif file_extension in ['.npy']:
            return self._read_numpy_image(progress_callback)

        elif file_extension in ['tif', 'tiff', '.tif', '.tiff']:
            return self._read_tiff_images(progress_callback)

        elif file_extension in ['.raw']:
            return self._read_raw_image(progress_callback)

        else:
            raise Exception('File format is not supported. Accepted formats include: .mhd, .mha, .npy, .tif, .raw')


    def write(self, out_fname):
        ''' writes to a file the image data produced by the read method
        Parameters
        ----------
        outfname: str
            filename or path where to save output image file.
            File extension will determine the type of file written.
        '''

        # call image writer
        
        # we may have just unmodified read in data
        # or we may have cropped data
        # or resampled data
        # HDF5 structure
        # have a single dataset saved with attributes:
        # attrs['original_fname'] = filepath to og data
        # attrs['original_shape'] = shape of og data
        # attrs['original_origin'] 
        # attrs['original_spacing']
        # attrs['resampled'] = bool
        # attrs['cropped'] = bool
        # attrs['spacing'] 
        # attrs['origin']

        # these will all be used in self.image_attrs
        # i.e. if no original_ prefix then they are about the saved dataset


    # just write to a hdf5 file or tiff + json

    # we want to save:
    # - downsampled image
    # - attributes about downsampled image which will include origin and spacing
    # - attributes of original image which will include original size

    def _read_meta_image(self, progress_callback=None):
        if self.resample:
            reader = cilMetaImageResampleReader()
            reader.SetTargetSize(int(self.target_size))

        elif self.crop:
            reader = cilMetaImageCroppedReader()
            reader.SetTargetZExtent(self.target_z_extent)
            self.image_attrs['resampled'] = False
            self.image_attrs['cropped'] = True

        else:
            reader = cilMetaImageResampleReader()
            # Forces use of resample reader but does not resample
            reader.SetTargetSize(int(1e12))
            self.image_attrs['resampled'] = False

        reader.SetFileName(self.file_name)
        reader.AddObserver(vtk.vtkCommand.ProgressEvent, partial(
                    self._report_progress, progress_callback=progress_callback))
        reader.Update()

        #output_image.ShallowCopy(reader.GetOutput())

        if self.resample:
            original_image_size = reader.GetStoredArrayShape(
            )[0] * reader.GetStoredArrayShape()[1] * reader.GetStoredArrayShape()[2]
            resampled_image_size = reader.GetTargetSize()
            if original_image_size <= resampled_image_size:
                self.image_attrs['resampled'] = False
            else:
                self.image_attrs['resampled'] = True

        original_shape = reader.GetStoredArrayShape()

        if not reader.GetIsFortran():
            original_shape = original_shape[::-1]

        self.image_attrs['original_shape'] = original_shape
        self.image_attrs['vol_bit_depth'] = str(reader.GetBytesPerElement()*8)
        self.image_attrs['isBigEndian'] = reader.GetBigEndian()
        self.image_attrs['header_length'] = 0

        return reader.GetOutput()

    def _read_numpy_image(self, progress_callback=None):
        if self.resample or self.crop:
            if self.resample:
                reader = cilNumpyResampleReader()
                reader.SetTargetSize(int(self.target_size))
                #output_image.ShallowCopy(reader.GetOutput())

            elif self.crop:
                reader = cilNumpyCroppedReader()
                reader.SetTargetZExtent(self.target_z_extent)
                self.image_attrs['cropped'] = True
                

            reader.SetFileName(self.file_name)
            reader.AddObserver(vtk.vtkCommand.ProgressEvent, partial(
                    self._report_progress, progress_callback=progress_callback))
            reader.Update()
            #output_image.ShallowCopy(reader.GetOutput())
            header_length = reader.GetFileHeaderLength()
            vol_bit_depth = reader.GetBytesPerElement()*8
            shape = reader.GetStoredArrayShape()
            if not reader.GetIsFortran():
                shape = shape[::-1]
            self.image_attrs['isBigEndian'] = reader.GetBigEndian()

            if self.resample:
                image_size = reader.GetStoredArrayShape(
                )[0] * reader.GetStoredArrayShape()[1]*reader.GetStoredArrayShape()[2]
                target_size = reader.GetTargetSize()

                if image_size <= target_size:
                    self.image_attrs['resampled'] = False
                else:
                    self.image_attrs['resampled'] = True

            output_image = reader.GetOutput()
            

        else:
            with open(self.file_name, 'rb') as f:
                header = f.readline()
            header_length = len(header)
            print("Length of header: ", len(header))

            numpy_array = numpy.load(self.file_name)
            shape = numpy.shape(numpy_array)

            if (isinstance(numpy_array[0][0][0], numpy.uint8)):
                vol_bit_depth = '8'
            elif(isinstance(numpy_array[0][0][0], numpy.uint16)):
                vol_bit_depth = '16'
            else:
                vol_bit_depth = None
                output_image = None
                return

            self.image_attrs['sampled'] = False
            if numpy_array.dtype.byteorder == '=':
                if sys.byteorder == 'big':
                    self.image_attrs['isBigEndian'] = True
                else:
                    self.image_attrs['isBigEndian'] = False
            else:
                self.image_attrs['isBigEndian'] = None

                print(self.image_attrs['isBigEndian'])
            
            output_image = vtk.vtkImageData()
            Converter.numpy2vtkImage(numpy_array, output=output_image)

        self.image_attrs["header_length"] = header_length
        self.image_attrs["vol_bit_depth"] = vol_bit_depth
        self.image_attrs["original_shape"] = shape
        # TODO: check
        print("read the numpy image")

        return output_image


    def _read_tiff_images(self, progress_callback=None):
        reader = vtk.vtkTIFFReader()
        filenames = glob.glob(os.path.join(self.file_name, '*'))

        if self.resample:
            raise NotImplementedError("Tiff resampling not yet implemented in this class")
        else:
            sa = vtk.vtkStringArray()
            for fname in filenames:
                i = sa.InsertNextValue(fname)
            print("read {} files".format(i))

            reader.AddObserver(vtk.vtkCommand.ProgressEvent, partial(
                self._report_progress, progress_callback=progress_callback))
            reader.SetFileNames(sa)
            reader.Update()

            numpy_array = Converter.vtk2numpy(reader.GetOutput())

            if self.image_attrs is not None:
                if (isinstance(numpy_array[0][0][0], numpy.uint8)):
                    self.image_attrs['vol_bit_depth'] = '8'
                elif(isinstance(numpy_array[0][0][0], numpy.uint16)):
                    self.image_attrs['vol_bit_depth'] = '16'
                print(self.image_attrs['vol_bit_depth'])

            self.image_attrs['sampled'] = False

            return reader.GetOutput()

    def _read_raw_image(self, progress_callback=None):
        if self.raw_image_attrs is None:
            raise Exception("To read a raw image, raw_image_attrs must be set.")


        # TODO: add checks of retrieval:
        dimensionality = len(self.raw_image_attrs['dimensions'])
        dimX = self.raw_image_attrs['dimensions'][0]
        dimY = self.raw_image_attrs['dimensions'][1]
        if dimensionality == 3:
            dimZ = self.raw_image_attrs['dimensions'][2]
        isFortran = self.raw_image_attrs['isFortran']
        isBigEndian = self.raw_image_attrs['isBigEndian']
        typecode = self.raw_image_attrs['typcode']
        
        self.image_attrs['isFortran'] = isFortran
        self.image_attrs['isBigEndian'] = isBigEndian
        self.image_attrs['typcode'] = typecode


        if dimensionality == 3:
            if isFortran:
                shape = (dimX, dimY, dimZ)
            else:
                shape = (dimZ, dimY, dimX)
        else:
            if isFortran:
                shape = (dimX, dimY)
            else:
                shape = (dimY, dimX)


        self.image_attrs["original_shape"] = shape

        if typecode == 0 or 1:
            self.image_attrs['vol_bit_depth'] = '8'
            bytes_per_element = 1
        else:
            self.image_attrs['vol_bit_depth'] = '16'
            bytes_per_element = 2

        # basic sanity check
        file_size = os.stat(self.file_name).st_size

        expected_size = 1
        for el in shape:
            expected_size *= el

        if typecode in [0, 1]:
            mul = 1
        elif typecode in [2, 3]:
            mul = 2
        elif typecode in [4, 5, 6]:
            mul = 4
        else:
            mul = 8
        expected_size *= mul
        if file_size != expected_size:
            errors = {"type": "size", "file_size": file_size,
                    "expected_size": expected_size}
            return (errors)

        if self.resample:
            reader = cilBaseResampleReader()
            reader.SetFileName(self.file_name)
            reader.SetTargetSize(int(self.target_size))
            reader.SetBytesPerElement(bytes_per_element)
            reader.SetBigEndian(isBigEndian)
            reader.SetIsFortran(isFortran)
            # TODO:
            # reader.SetRawTypeCode(raw_type_code)
            reader.SetRawTypeCode(typecode)
            reader.SetStoredArrayShape(shape)


        elif self.crop:
            reader = cilBaseCroppedReader()
            reader.SetFileName(self.file_name)
            reader.SetTargetZExtent(self.target_z_extent)
            #reader.SetOrigin(tuple(origin))
            reader.SetBytesPerElement(bytes_per_element)
            reader.SetBigEndian(isBigEndian)
            reader.SetIsFortran(isFortran)
            reader.SetRawTypeCode(typecode)
            reader.SetStoredArrayShape(shape)

            self.image_attrs['cropped'] = True

        else:
            self.image_attrs['sampled'] = False

            reader = cilBaseResampleReader()
            reader.SetFileName(self.file_name)
            reader.SetTargetSize(1e12)
            reader.SetBytesPerElement(bytes_per_element)
            reader.SetBigEndian(isBigEndian)
            reader.SetIsFortran(isFortran)
            reader.SetRawTypeCode(typecode)
            reader.SetStoredArrayShape(shape)


        reader.AddObserver(vtk.vtkCommand.ProgressEvent, partial(
                    self._report_progress, progress_callback=progress_callback))
        reader.Update()

        image_size = reader.GetStoredArrayShape(
            )[0] * reader.GetStoredArrayShape()[1]*reader.GetStoredArrayShape()[2]
        if self.resample:
            target_size = reader.GetTargetSize()
            print("array shape", image_size)
            print("target", target_size)
            if image_size <= target_size:
                self.image_attrs['sampled'] = False
            else:
                self.image_attrs['sampled'] = True

            return reader.GetOutput()

    def _set_up_logger(self, fname):
        """Set up the logger """
        if fname:
            print("Will output results to: " +  fname)
            handler = logging.FileHandler(fname)
            self.logger = logging.getLogger("ImageReader")
            self.logger.setLevel(logging.INFO)
            self.logger.addHandler(handler)


    def _report_progress(self, caller, event, progress_callback):
        ''' This emits the progress as an integer between 1 and 100, if a 
        Qt progress_callback has been passed. This allows progress to be kept track
        of if the reading is run in a Worker thread.'''
        #TODO: test log
        self.logger.info(str(caller.getProgress()*100) + "%")

        if progress_callback is not None:
            progress_callback.emit(int(caller.getProgress()*100))


class ImageWriter(object):

    def __init__(self, **kwargs):