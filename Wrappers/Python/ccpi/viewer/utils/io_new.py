import datetime
import glob
import imghdr
import logging
import os
import shutil
import sys
import time
from functools import partial

import h5py
import numpy as np
import vtk
from ccpi.viewer.iviewer import iviewer
from ccpi.viewer.utils import Converter
from ccpi.viewer.utils.conversion import (HDF5SubsetReader,
                                          cilBaseCroppedReader,
                                          cilBaseResampleReader,
                                          cilHDF5ResampleReader,
                                          cilMetaImageCroppedReader,
                                          cilMetaImageResampleReader,
                                          cilNumpyCroppedReader,
                                          cilNumpyResampleReader,
                                          parseNpyHeader)
from ccpi.viewer.utils.hdf5_io import HDF5Reader
from ccpi.viewer.version import version
from schema import Optional, Or, Schema, SchemaError
from vtk.numpy_interface import dataset_adapter as dsa

# Currently doesn't support both cropping and resampling
# If set both to true then it resamples and doesn't crop


# TODO: make auto progress bar instead of from readers

# write:
#


class ImageReader(object):

    def __init__(self, **kwargs):
        '''
        Constructor

        Parameters
        ----------
        file_name: os.path or string, default None
            file name to read
        resample: bool, default True
            whether to resample
        crop: bool, default False
            whether to crop
        target_size: int, default 512**3
            target size after downsampling
        target_z_extent: list [,], default None
            desired extent after cropping on z axis
        raw_image_attrs: dict, default None
            Attributes of the raw image data, must have the format:
            {'dimensions': 2D or 3D array, 'is_fortran':bool, 'is_big_endian':bool
            'type_code':info_var['typcode']}
        hdf5_image_attrs: dict, default {'dataset_name': entry1/tomo_entry/data/data, 'is_acquisition_data': True}
            Attributes of the hdf5 image data, all entries are optional - if not set they will fall back to
            defaults. Format: {'dataset_name': str, 'is_acquisition_data':bool}, 
            
        '''
        file_name = kwargs.get('file_name', None)
        resample = kwargs.get('resample', True)
        target_size = kwargs.get('target_size', 512**3)
        crop = kwargs.get('crop', False)
        target_z_extent = kwargs.get('target_z_extent', None)
        raw_image_attrs = kwargs.get('raw_image_attrs', None)
        hdf5_image_attrs = kwargs.get('hdf5_image_attrs', None)

        if file_name is not None:
            self.set_up(file_name, resample, target_size,
                        crop, target_z_extent, raw_image_attrs, hdf5_image_attrs)

    def set_up(self,  file_name=None, resample=True, target_size=512**3, crop=False,
        target_z_extent=None, raw_image_attrs=None, hdf5_image_attrs=None):

        if file_name is None:
            raise Exception('Path to file is required.')

        if not (os.path.isfile(file_name) or os.path.isdir(file_name)):
            raise Exception('Path\n {}\n does not exist.'.format(file_name))

        self.file_name = file_name
        self.resample = resample
        self.target_size = target_size
        self.crop = crop
        self.target_z_extent = target_z_extent
        if self.crop and self.resample:
            # TODO: check if this is true
            print("WARNING: Both cropping and resampling is not yet implemented.")
            print("Image will just be resampled and not cropped.")
            self.crop = False
        # validate image attributes
        raw_attrs = None
        hdf5_attrs=None
        if raw_image_attrs is not None and raw_image_attrs != {}:
            try:
                raw_attrs = self._validate_raw_attrs(raw_image_attrs)
            except SchemaError as e:
                raise ValueError("Error: Raw image attributes were not input correctly: ", e)
        if hdf5_image_attrs is not None and hdf5_image_attrs != {}:
            try:
                hdf5_attrs = self._validate_hdf5_attrs(hdf5_image_attrs)
            except SchemaError as e:
                raise ValueError("Error: HDF5 image attributes were not input correctly: ", e)

        self.original_image_attrs = self._generate_image_attrs(raw_attrs, hdf5_attrs)
        self.loaded_image_attrs = {'resampled': self.resample, 'cropped': self.crop}

            
    def _validate_raw_attrs(self, raw_image_attrs):
        if raw_image_attrs is None:
            return
        raw_attrs = raw_image_attrs.copy()
        raw_attrs_schema = Schema({'dimensions': Or(list, np.ndarray, tuple),
                                   'is_fortran': bool,
                                   'is_big_endian': bool,
                                   'typecode': str})
        # TODO: add list of possible typecodes to schema
        raw_attrs_schema.validate(raw_attrs)
        return raw_attrs

    def _validate_hdf5_attrs(self, hdf5_image_attrs):
        if hdf5_image_attrs is None:
            return
        hdf5_attrs = hdf5_image_attrs.copy()
        hdf5_attrs_schema = Schema({Optional('dataset_name', default="entry1/tomo_entry/data/data"): str,
                                   Optional('is_acquisition_data', default=True): bool, Optional(str): object})
        hdf5_attrs = hdf5_attrs_schema.validate(hdf5_attrs)
        return hdf5_attrs


    def _generate_image_attrs(self, raw_image_attrs=None, hdf5_image_attrs=None):
        image_attrs = {}
        if raw_image_attrs is not None:
            image_attrs.update(raw_image_attrs)
        if hdf5_image_attrs is not None:
            image_attrs.update(hdf5_image_attrs)
        image_attrs['file_name'] = self.file_name
        return image_attrs

    def get_original_attrs(self):
        return self.original_image_attrs

    def get_loaded_attrs(self):
        return self.loaded_image_attrs

    def read(self, *args, **kwargs):
        ''' reads self.file_name
            returns vtkImageData'''
        # identifies file type
        # uses appropriate reader based on file type and cropping or resampling

        self._data = None  # overwrite any previously read data

        if os.path.isfile(self.file_name):
            file_extension = os.path.splitext(self.file_name)[1]

            if file_extension in ['.mha', '.mhd']:
                self._data = self._read_meta_image()

            elif file_extension in ['.npy']:
                self._data = self._read_numpy_image()

            elif file_extension in ['tif', 'tiff', '.tif', '.tiff']:
                self._data = self._read_tiff_images()

            elif file_extension in ['.raw']:
                self._data = self._read_raw_image()

            elif file_extension in ['.nxs', '.h5', '.hdf5']:
                self._data = self._read_hdf5_image()

            elif file_extension in ['.tif', '.tiff']:
                image_files = glob.glob(os.path.join(os.path.dirname(self.file_name), '*.{}'.format(file_extension)))
                if len(image_files) == 0:
                    raise Exception('No tiff files were found in: {}'.format(self.file_name))
                self._data = self._read_tiff_images(image_files)

            else:
                raise Exception(
                    'File format is not supported. Accepted formats include: .mhd, .mha, .npy, .tif, .raw')
        
        else: # If we are given a folder, not a file, look for tiff files and try to read them
            image_files = glob.glob(os.path.join(self.file_name, '*.tif')) + glob.glob(os.path.join(self.file_name, '*.tiff'))
            if len(image_files) == 0:
                raise Exception('No tiff files were found in: {}'.format(self.file_name))
            self._data = self._read_tiff_images(image_files)

        self.loaded_image_attrs['origin'] = self._data.GetOrigin()
        self.loaded_image_attrs['spacing'] = self._data.GetSpacing()
        self.loaded_image_attrs['shape'] = self._data.GetDimensions()
        print(self._data)
        

        return self._data

    def write(self, out_fname):
        ''' writes to a file the image data produced by the read method
        Parameters
        ----------
        outfname: str
            filename or path where to save output image file.
            File extension will determine the type of file written.
        '''
        if not hasattr(self, '_data_read') or self._data is None:
            raise Exception(
                "Can't write before reading the data. Call read() first.")

        # we may have just unmodified read in data
        # or we may have cropped data
        # or resampled data
        # HDF5 structure
        # have a single dataset saved with attributes:
        # DONE attrs['original_fname'] = filepath to og data
        # DONE attrs['original_shape'] = shape of og data
        # DONE attrs['original_origin']
        # DONE attrs['original_spacing']
        # DONE attrs['resampled'] = bool
        # DONE attrs['cropped'] = bool
        # attrs['spacing']
        # attrs['origin']

        # these will all be used in self.original_image_attrs
        # i.e. if no original_ prefix then they are about the saved dataset

    # just write to a hdf5 file or tiff + json

    # we want to save:
    # - downsampled image
    # - attributes about downsampled image which will include origin and spacing
    # - attributes of original image which will include original size

    def _read_meta_image(self):
        if self.resample:
            reader = cilMetaImageResampleReader()
            reader.SetTargetSize(int(self.target_size))

        elif self.crop:
            reader = cilMetaImageCroppedReader()
            reader.SetTargetZExtent(tuple(self.target_z_extent))
            self.loaded_image_attrs['resampled'] = False

        else:
            reader = cilMetaImageResampleReader()
            # Forces use of resample reader but does not resample
            reader.SetTargetSize(int(1e12))

        reader.SetFileName(self.file_name)
        # reader.AddObserver(vtk.vtkCommand.ProgressEvent, partial(
        #             self._report_progress, progress_callback=progress_callback))
        reader.Update()

        # output_image.ShallowCopy(reader.GetOutput())

        if self.resample:
            original_image_size = reader.GetStoredArrayShape(
            )[0] * reader.GetStoredArrayShape()[1] * reader.GetStoredArrayShape()[2]
            resampled_image_size = reader.GetTargetSize()
            if original_image_size <= resampled_image_size:
                self.loaded_image_attrs['resampled'] = False

        original_shape = reader.GetStoredArrayShape()

        if not reader.GetIsFortran():
            original_shape = original_shape[::-1]

        self.original_image_attrs['shape'] = original_shape
        self.original_image_attrs['vol_bit_depth'] = str(reader.GetBytesPerElement()*8)
        self.original_image_attrs['is_big_endian'] = reader.GetBigEndian()
        self.original_image_attrs['header_length'] = 0
        self.original_image_attrs['origin'] = reader.GetOrigin()

        return reader.GetOutput()

    def _read_numpy_image(self):
        ''' Reads a self.file_name as a numpy image file and may resample or
         crop depending on whether self.resample or self.crop are set.
        Returns
        -------
        vtkImageData:
            containing the image data.'''
        print("going to read numpy")
        if self.resample or self.crop:
            if self.resample:
                reader = cilNumpyResampleReader()
                reader.SetTargetSize(int(self.target_size))

            elif self.crop:
                reader = cilNumpyCroppedReader()
                reader.SetTargetZExtent(tuple(self.target_z_extent))
                self.loaded_image_attrs['cropped'] = True

            reader.SetFileName(self.file_name)
            # reader.AddObserver(vtk.vtkCommand.ProgressEvent, partial(
            #         self._report_progress, progress_callback=progress_callback))
            reader.Update()
            # output_image.ShallowCopy(reader.GetOutput())
            header_length = reader.GetFileHeaderLength()
            vol_bit_depth = reader.GetBytesPerElement()*8
            shape = reader.GetStoredArrayShape()
            if not reader.GetIsFortran():
                shape = shape[::-1]
            self.loaded_image_attrs['isBigEndian'] = reader.GetBigEndian()

            if self.resample:
                image_size = reader.GetStoredArrayShape(
                )[0] * reader.GetStoredArrayShape()[1]*reader.GetStoredArrayShape()[2]
                target_size = reader.GetTargetSize()

                if image_size <= target_size:
                    self.loaded_image_attrs['resampled'] = False

            output_image = reader.GetOutput()

        else:
            with open(self.file_name, 'rb') as f:
                header = f.readline()
            header_length = len(header)
            print("Length of header: ", len(header))

            numpy_array = np.load(self.file_name)
            shape = np.shape(numpy_array)

            if (isinstance(numpy_array[0][0][0], np.uint8)):
                vol_bit_depth = '8'
            elif(isinstance(numpy_array[0][0][0], np.uint16)):
                vol_bit_depth = '16'
            else:
                vol_bit_depth = None
                output_image = None

            self.loaded_image_attrs['resampled'] = False

            output_image = vtk.vtkImageData()
            Converter.numpy2vtkImage(numpy_array, output=output_image)

        self.original_image_attrs["header_length"] = header_length
        self.original_image_attrs["vol_bit_depth"] = vol_bit_depth
        self.original_image_attrs["shape"] = shape
        self.original_image_attrs['origin'] = [0, 0, 0] # Can't save origin to numpy file
        self.original_image_attrs['spacing'] = [1, 1, 1] # Can't save spacing to numpy file

        return output_image

    def _read_tiff_images(self, filenames):
        reader = vtk.vtkTIFFReader()

        if self.resample:
            # raise NotImplementedError(
            #     "Tiff resampling not yet implemented in this class")
            print("WARNING: Tiff resampling is not yet implemented, so image won't be resampled.")
            self.resample = False

        sa = vtk.vtkStringArray()
        for fname in filenames:
            i = sa.InsertNextValue(fname)
        print("read {} files".format(i))

        # reader.AddObserver(vtk.vtkCommand.ProgressEvent, partial(
        #     getProgress, progress_callback=progress_callback))
        reader.SetFileNames(sa)
        reader.Update()

        numpy_array = Converter.vtk2numpy(reader.GetOutput())

        if self.original_image_attrs is not None:
            if (isinstance(numpy_array[0][0][0], np.uint8)):
                self.original_image_attrs['vol_bit_depth'] = '8'
            elif(isinstance(numpy_array[0][0][0], np.uint16)):
                self.original_image_attrs['vol_bit_depth'] = '16'
            print(self.original_image_attrs['vol_bit_depth'])

        self.loaded_image_attrs['resampled'] = False

        return reader.GetOutput()

    def _read_raw_image(self):
        print("when we read: ", self.original_image_attrs)
        if self.original_image_attrs is None or 'dimensions' not in self.original_image_attrs.keys():
            raise Exception(
                "To read a raw image, raw_image_attrs must be set.")

        # TODO: add checks of retrieval:
        dimensionality = len(self.original_image_attrs['dimensions'])
        dimX = self.original_image_attrs['dimensions'][0]
        dimY = self.original_image_attrs['dimensions'][1]
        if dimensionality == 3:
            dimZ = self.original_image_attrs['dimensions'][2]
        isFortran = self.original_image_attrs['is_fortran']
        isBigEndian = self.original_image_attrs['is_big_endian']
        typecode = self.original_image_attrs['typecode']

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

        self.original_image_attrs["original_shape"] = shape

        if typecode == 0 or 1:
            self.original_image_attrs['vol_bit_depth'] = '8'
            bytes_per_element = 1
        else:
            self.original_image_attrs['vol_bit_depth'] = '16'
            bytes_per_element = 2

        # basic sanity check
        file_size = os.stat(self.file_name).st_size

        expected_size = 1
        for el in shape:
            expected_size *= el

        if typecode in ["uint8", "int8"]:
            mul = 1
        elif typecode in ["uint16", "int16"]:
            mul = 2
        elif typecode in ["uint32", "int32"]:
            mul = 4
        else:
            mul = 8
        expected_size *= mul
        if file_size != expected_size:
            errors = {"type": "size", "file_size": file_size,
                      "expected_size": expected_size}
            raise Exception("Error with loading file: {}. Expected size: {}, Actual Size: {}.".format(self.file_name, file_size, expected_size))

        if self.resample:
            reader = cilBaseResampleReader()
            reader.SetFileName(self.file_name)
            reader.SetTargetSize(int(self.target_size))
            reader.SetBytesPerElement(bytes_per_element)
            reader.SetBigEndian(isBigEndian)
            reader.SetIsFortran(isFortran)
            reader.SetRawTypeCode(typecode)
            reader.SetStoredArrayShape(shape)

        elif self.crop:
            reader = cilBaseCroppedReader()
            reader.SetFileName(self.file_name)
            reader.SetTargetZExtent(self.target_z_extent)
            # reader.SetOrigin(tuple(origin))
            reader.SetBytesPerElement(bytes_per_element)
            reader.SetBigEndian(isBigEndian)
            reader.SetIsFortran(isFortran)
            reader.SetRawTypeCode(typecode)
            reader.SetStoredArrayShape(shape)

            self.original_image_attrs['cropped'] = True

        else:
            self.original_image_attrs['resampled'] = False

            reader = cilBaseResampleReader()
            reader.SetFileName(self.file_name)
            reader.SetTargetSize(1e12)
            reader.SetBytesPerElement(bytes_per_element)
            reader.SetBigEndian(isBigEndian)
            reader.SetIsFortran(isFortran)
            reader.SetRawTypeCode(typecode)
            reader.SetStoredArrayShape(shape)

        # reader.AddObserver(vtk.vtkCommand.ProgressEvent, partial(
        #             self._report_progress, progress_callback=progress_callback))
        reader.Update()

        image_size = reader.GetStoredArrayShape(
        )[0] * reader.GetStoredArrayShape()[1]*reader.GetStoredArrayShape()[2]
        if self.resample:
            target_size = reader.GetTargetSize()
            print("array shape", image_size)
            print("target", target_size)
            if image_size <= target_size:
                self.original_image_attrs['resampled'] = False
            else:
                self.original_image_attrs['resampled'] = True

        return reader.GetOutput()

    def _read_hdf5_image(self):
        if self.original_image_attrs is None or 'dataset_name' not in self.original_image_attrs.keys():
            # Fall back to default hdf5 attributes if none have been set.
            hdf5_attrs = self._validate_hdf5_attrs({})
            print("the h5 attrs: ", self.original_image_attrs)
            self.original_image_attrs = self._generate_image_attrs(hdf5_image_attrs=hdf5_attrs)
            print("the h5 attrs: ", self.original_image_attrs)

        if self.resample:
            reader = cilHDF5ResampleReader()
            reader.SetTargetSize(int(self.target_size))
            reader.SetFileName(self.file_name)
            reader.SetDatasetName(self.original_image_attrs['dataset_name'])
            reader.SetIsAcquisitionData(self.original_image_attrs['is_acquisition_data'])

        elif self.crop:
            full_reader = HDF5Reader()
            full_reader.SetFileName(self.file_name)
            full_reader.SetDatasetName(self.original_image_attrs['dataset_name'])
            reader = HDF5SubsetReader()
            reader.SetInputConnection(full_reader.GetOutputPort())
            extent = [0, -1, 0, -1, self.target_z_extent[0], self.target_z_extent[1]]
            reader.SetUpdateExtent(extent)

        else:
            reader = cilHDF5ResampleReader()
            reader.SetTargetSize(int(self.target_size*1e12))
            reader.SetFileName(self.file_name)
            reader.SetDatasetName(self.original_image_attrs['dataset_name'])
        
        
        reader.Update()


        if self.resample:
            image_size = reader.GetStoredArrayShape(
                )[0] * reader.GetStoredArrayShape()[1]*reader.GetStoredArrayShape()[2]
            target_size = reader.GetTargetSize()
            print("array shape", image_size)
            print("target", target_size)
            if image_size <= target_size:
                self.loaded_image_attrs['resampled'] = False

        if not self.crop:
            self.original_image_attrs['origin'] = reader.GetOrigin()
            self.original_image_attrs['spacing'] = reader.GetElementSpacing()
            self.original_image_attrs['shape'] = reader.GetStoredArrayShape()
            print("numpy code: ", reader.GetNumpyTypeCode())
            self.loaded_image_attrs['typecode'] = reader.GetNumpyTypeCode()
            self.original_image_attrs['typecode'] = reader.GetNumpyTypeCode()
            print("WE CROPPED")
        else:
            self.original_image_attrs['origin'] = full_reader.GetOrigin()
            # TODO fix getting this stuff:
            # self.original_image_attrs['spacing'] = full_reader.GetElementSpacing()
            # self.original_image_attrs['shape'] = full_reader.GetStoredArrayShape()
            # print("numpy code: ", full_reader.GetNumpyTypeCode())
            # self.loaded_image_attrs['typecode'] = full_reader.GetNumpyTypeCode()
            # self.original_image_attrs['typecode'] = full_reader.GetNumpyTypeCode()

        self.loaded_image_attrs['vtk_array_name'] = 'entry1/tomo_entry/data/data' # TODO FIX!!

        

        return reader.GetOutputDataObject(0)


    # TODO: test logger
    def _set_up_logger(self, fname):
        """Set up the logger """
        if fname:
            print("Will output results to: " + fname)
            handler = logging.FileHandler(fname)
            self.logger = logging.getLogger("ImageReader")
            self.logger.setLevel(logging.INFO)
            self.logger.addHandler(handler)

    def _report_progress(self, caller, event, progress_callback):
        ''' This emits the progress as an integer between 1 and 100, if a 
        Qt progress_callback has been passed. This allows progress to be kept track
        of if the reading is run in a Worker thread.'''
        # TODO: test log
        self.logger.info(str(caller.getProgress()*100) + "%")

        if progress_callback is not None:
            progress_callback.emit(int(caller.getProgress()*100))


class ImageWriter(object):

    def __init__(self, **kwargs):
        file_name = kwargs.get('file_name', None)
        datasets = kwargs.get('datasets', True)

        # can have multiple datasets
        # so we want to input list of datasets and their attributes and optionally the data
        # so we have
        # datasets = [[dataset, attributes], [dataset1, attributes1]] and they're auto written to entry1, entry2 etc.
        # if dataset entry is None we must have an attribute filename

        self.set_up(file_name, datasets)

    def set_up(self, filename, datasets):
        self.file_name = filename
        self.datasets = datasets


    def write(self):
        # check file ext

            file_extension = os.path.splitext(self.file_name)[1]

            if file_extension in ['tif', 'tiff', '.tif', '.tiff']:
                self._write_tiff()

            elif file_extension in ['.nxs', '.h5', '.hdf5']:
                self._write_hdf5()

            elif file_extension in ['']:
                self.file_name = self.file_name + '.nxs'
                self._write_hdf5()

            else:
                raise Exception("File format is not supported. Supported types include tiff and hdf5/nexus.")


    def _write_hdf5(self):
        with h5py.File(self.file_name, 'w') as f:
            
            # give the file some important attributes
            f.attrs['file_name'] = self.file_name
            f.attrs['cilviewer_version'] = version
            f.attrs['file_time'] = str(datetime.datetime.utcnow())
            f.attrs['creator'] = np.string_('io.py')
            f.attrs['HDF5_Version'] = h5py.version.hdf5_version
            f.attrs['h5py_version'] = h5py.version.version
            
            # create the NXentry group
            nxentry = f.create_group('entry1/tomo_entry')
            nxentry.attrs['NX_class'] = 'NXentry'


            for i, dataset in enumerate(self.datasets):
                entry_num = i+1
                data = dataset[0]
                dataset_info = dataset[1]
                dataset_name = 'entry{}/tomo_entry/data/data'.format(entry_num)

                vtk_array_name = dataset_info.get('vtk_array_name', 'vtkarray')

                if data is not None:
                    wdata = dsa.WrapDataObject(data)
                    array = wdata.PointData[vtk_array_name]
                    # Note that we flip the dimensions here because
                    # VTK's order is Fortran whereas h5py writes in
                    # C order. We don't want to do deep copies so we write
                    # with dimensions flipped and pretend the array is
                    # C order.
                    array = array.reshape(wdata.GetDimensions()[::-1])
                else:
                    array = None
                try:
                    if array is None:
                        dset = f.create_dataset(dataset_name, dataset_info['shape'], dataset_info['typecode'])
                    else:
                        dset = f.create_dataset(dataset_name, data=array, dtype= dataset_info['typecode'])
                except RuntimeError:
                        print("Unable to save image data to {0}."
                            "Dataset with name {1} already exists in this file.".format(
                                self.file_name, dataset_name))
                

                for key, value in dataset_info.items():
                    if 'vtk_array_name' not in key and 'typecode' not in key:
                        dset.attrs[key] = value

            #[0,1,2,3]

            #create data entry
            #original_data = 


            # # data attributes:
            # # original dataset will be in 'entry1/tomo_entry/data/data'
            
            # original_data.attrs['original_fname'] = filepath to original data
            # original_data.attrs['original_shape'] = shape of  original  data
            # original_data.attrs['original_origin'] =
            # original_data.attrs['original_spacing'] =

            # # downsampled or cropped (or both) will be in: 'entry2/tomo_entry/data/data'
            # modified_data.attrs['resampled'] = bool
            # modified_data.attrs['cropped'] = bool
            # modified_data.attrs['spacing'] =
            # modified_data.attrs['origin']=

        def _write_tiff(self):
            pass


def descend_obj(obj, sep='\t'):
    """
    Iterate through groups in a HDF5 file and prints the groups and datasets names and datasets attributes
    """
    if type(obj) in [h5py._hl.group.Group, h5py._hl.files.File]:
        for key in obj.keys():
            print(sep, '-', key, ':', obj[key])
            descend_obj(obj[key], sep=sep+'\t')
    elif type(obj) == h5py._hl.dataset.Dataset:
        for key in obj.attrs.keys():
            print(sep+'\t', '-', key, ':', obj.attrs[key])


def h5dump(path, group='/'):
    """
    print HDF5 file metadata

    group: you can give a specific group, defaults to the root group
    """
    print("dump")
    with h5py.File(path, 'r') as f:
        descend_obj(f[group])

if __name__ == "__main__":
    reader = ImageReader(file_name=r"C:\Users\lhe97136\Work\Data\24737_fd_normalised.nxs", crop=True, resample=False, target_z_extent=[1, 2], hdf5_image_attrs={'is_acquisition_data': False})
    img=reader.read()
    iviewer(img, img)
    original_image_attrs = reader.get_original_attrs()
    loaded_image_attrs = reader.get_loaded_attrs()
    writer = ImageWriter(file_name='test_empty_dataset.hdf5', datasets=[[None, original_image_attrs], [img, loaded_image_attrs]])
    writer.write()
    h5dump('test_empty_dataset.hdf5')

    # Entrypoint:
    # - take args
    # - read file
    # - write file




    # reader2 = ImageReader(file_name=r"C:\Users\lhe97136\Work\Data\24737_fd_normalised.nxs", hdf5_image_attrs={'dataset_name': 'entry2/tomo_entry/data/data'})
    # img2=reader.read()
    # original_image_attrs2 = reader.get_original_attrs()
    # loaded_image_attrs2 = reader.get_loaded_attrs()

    # print(img)
    # print(img2)
