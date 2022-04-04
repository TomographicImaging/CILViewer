import datetime
import glob
import imghdr
import logging
import os
import shutil
import sys
import time
from functools import partial

from attr import attributes
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase

import h5py
import numpy as np
import vtk
from ccpi.viewer.iviewer import iviewer
from ccpi.viewer.utils import Converter
from ccpi.viewer.utils.conversion import (HDF5SubsetReader,
                                          cilRawCroppedReader,
                                          cilRawResampleReader,
                                          cilHDF5CroppedReader,
                                          cilHDF5ResampleReader,
                                          cilMetaImageCroppedReader,
                                          cilMetaImageResampleReader,
                                          cilNumpyCroppedReader,
                                          cilNumpyResampleReader)
from ccpi.viewer.utils.hdf5_io import HDF5Reader
from ccpi.viewer.version import version
from schema import Optional, Or, Schema, SchemaError
from vtk.numpy_interface import dataset_adapter as dsa
from ccpi.viewer.utils.error_handling import customise_warnings
from ccpi.viewer.utils.hdf5_io import HDF5Reader

import warnings

# Currently doesn't support both cropping and resampling
# If set both to true then it resamples and doesn't crop


# TODO: progress reporting
# supporting tiffs
# logger


# write other filetypes
# possibly change structure of how it's written out
# make a reader for our data format that we write out


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
        resample_z: bool, default True
            whether to resample on the z axis. E.g. in the case we have
            acquisition data, the projections would be on the z axis, so
            we would not want to resample in that direction.
        raw_image_attrs: dict, default None
            Attributes of the raw image data, must have the format:
            {'shape': 2D or 3D array, 'is_fortran':bool, 'is_big_endian':bool
            'type_code':info_var['typcode']}
        hdf5_dataset_name: string, default "entry1/tomo_entry/data/data"
            Name of the hdf5 dataset to be read, if file format is hdf5
        log_file: str, optional, default None
            log verbose output to file of this name            
        '''
        file_name = kwargs.get('file_name')
        resample = kwargs.get('resample', True)
        target_size = kwargs.get('target_size', 512**3)
        crop = kwargs.get('crop', False)
        target_z_extent = kwargs.get('target_z_extent')
        resample_z = kwargs.get('resample_z', False)
        raw_image_attrs = kwargs.get('raw_image_attrs')
        hdf5_dataset_name = kwargs.get('hdf5_dataset_name', "entry1/tomo_entry/data/data")
        log_file = kwargs.get('log_file')

        if file_name is not None:
            self.set_up(file_name, resample, target_size,
                        crop, target_z_extent, resample_z, raw_image_attrs, hdf5_dataset_name, log_file)

    def set_up(self,  file_name=None, resample=True, target_size=512**3, crop=False,
        target_z_extent=None, resample_z=False, raw_image_attrs=None, hdf5_dataset_name="entry1/tomo_entry/data/data", 
        log_file=None):

        customise_warnings()

        self._set_up_logger(log_file)

        if file_name is None:
            raise Exception('Path to file is required.')

        if not (os.path.isfile(file_name) or os.path.isdir(file_name)):
            raise Exception('Path\n {}\n does not exist.'.format(file_name))

        self.file_name = file_name
        self.resample = resample
        self.target_size = target_size
        self.crop = crop
        self.target_z_extent = target_z_extent
        self.resample_z = resample_z
        self.hdf5_dataset_name = hdf5_dataset_name

        # validate image attributes
        raw_attrs = None
        if raw_image_attrs is not None and raw_image_attrs != {}:
            try:
                raw_attrs = self._validate_raw_attrs(raw_image_attrs)
            except SchemaError as e:
                raise ValueError("Error: Raw image attributes were not input correctly: ", e)

        self.original_image_attrs = self._generate_image_attrs(raw_attrs)
        self.loaded_image_attrs = {'resampled': self.resample, 'cropped': self.crop}

        if self.crop:
            if self.target_z_extent is None:
                raise Exception("Error: if crop is set to True, target_z_extent must be set.")

        if self.crop and self.resample:
            warnings.warn("Both cropping and resampling is not yet implemented. Image will just be cropped and not resampled.")
            self.resample = False
        
       
    def _validate_raw_attrs(self, raw_image_attrs):
        if raw_image_attrs is None:
            return
        raw_attrs = raw_image_attrs.copy()
        raw_attrs_schema = Schema({'shape': Or(list, np.ndarray, tuple),
                                   'is_fortran': bool,
                                   'is_big_endian': bool,
                                   'typecode': str})
        raw_attrs_schema.validate(raw_attrs)
        return raw_attrs


    def _generate_image_attrs(self, raw_image_attrs=None, hdf5_image_attrs=None):
        image_attrs = {}
        if raw_image_attrs is not None:
            image_attrs.update(raw_image_attrs)
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

        # progress_callback = kwargs.get('progress_callback')
        # print("The progress callback: ", progress_callback)

        self.logger.info("read: {}".format(self.file_name))

        if os.path.isfile(self.file_name):
            file_extension = os.path.splitext(self.file_name)[1]

            if file_extension in ['.mha', '.mhd']:
                reader = self._get_meta_image_reader()

            elif file_extension in ['.npy']:
                reader = self._get_numpy_image_reader()

            elif file_extension in ['.raw']:
                reader = self._read_raw_image()

            elif file_extension in ['.nxs', '.h5', '.hdf5']:
                reader = self._get_hdf5_image_reader()
                self.original_image_attrs['dataset_name'] = self.hdf5_dataset_name

            # elif file_extension in ['.tif', '.tiff']:
            #     image_files = glob.glob(os.path.join(os.path.dirname(self.file_name), '*.{}'.format(file_extension)))
            #     if len(image_files) == 0:
            #         raise Exception('No tiff files were found in: {}'.format(self.file_name))
            #     self._data = self._read_tiff_images(image_files)

            else:
                raise Exception('File format is not supported. Accepted formats include: .mhd, .mha, .npy, .tif, .raw')
        else: # If we are given a folder, not a file, look for tiff files and try to read them
            image_files = glob.glob(os.path.join(self.file_name, '*.tif')) + glob.glob(os.path.join(self.file_name, '*.tiff'))
            if len(image_files) == 0:
                raise Exception('No tiff files were found in: {}'.format(self.file_name))
            self._data = self._read_tiff_images(image_files)

        reader.SetFileName(self.file_name)
        self.logger.debug("is it acq? : {}".format(self.resample_z))
        reader.SetIsAcquisitionData(self.resample_z)
        if not self.crop:
            if self.resample:
                target_size = self.target_size
            else:
                # forced use of resample reader in the case that we 
                # don't want to crop or resample,
                # but the large target size means we don't resample
                target_size = 1e12
            reader.SetTargetSize(int(target_size))
        reader.Update()
        data = reader.GetOutput()
        
        # Make sure whether we did resample or not:
        if self.resample:
            original_image_size = reader.GetStoredArrayShape(
            )[0] * reader.GetStoredArrayShape()[1] * reader.GetStoredArrayShape()[2]
            resampled_image_size = reader.GetTargetSize()
            if original_image_size <= resampled_image_size:
                self.loaded_image_attrs['resampled'] = False
            else:
                self.loaded_image_attrs['resampled'] = True

        # info about original dataset:
        self.original_image_attrs['shape'] = reader.GetStoredArrayShape()
        self.original_image_attrs['spacing'] = reader.GetElementSpacing()
        self.original_image_attrs['origin'] = reader.GetOrigin()
        self.original_image_attrs['bit_depth'] = str(reader.GetBytesPerElement()*8)
        self.original_image_attrs['is_big_endian'] = reader.GetBigEndian()
        self.original_image_attrs['header_length'] = reader.GetFileHeaderLength()
        # TODO: here we need to save the filepath of the original dataset

        # info about new dataset:
        self.loaded_image_attrs['spacing'] = data.GetSpacing()
        self.loaded_image_attrs['origin'] = data.GetOrigin()
        self.loaded_image_attrs['vtk_array_name'] = 'ImageScalars'
        if self.resample:
            self.loaded_image_attrs['resample_z'] = self.resample_z
        # TODO: do we need to set typecode in case we want to write to hdf5 self.loaded_image_attrs['typecode']  ??
        
        return data

    def get_original_image_attributes(self):
        return self.original_image_attrs

    def get_loaded_image_attrs(self):
        return self.loaded_image_attrs

    def _get_meta_image_reader(self, progress_callback=None):
        if self.crop:
            reader = cilMetaImageCroppedReader()
            reader.SetTargetZExtent(tuple(self.target_z_extent))
        else:
            reader = cilMetaImageResampleReader()
        return reader

    def _get_numpy_image_reader(self, progress_callback=None):
        if self.crop:
            reader = cilNumpyCroppedReader()
            reader.SetTargetZExtent(tuple(self.target_z_extent))
        else:
            reader = cilNumpyResampleReader()

        return reader


    def _read_tiff_images(self, progress_callback=None):
        # TODO!!!!!!!!!!!
        reader = vtk.vtkTIFFReader()
        filenames = glob.glob(os.path.join(self.file_name, '*'))

        if self.resample:
            raise NotImplementedError("Tiff resampling not yet implemented in this class")

        sa = vtk.vtkStringArray()
        for fname in filenames:
            i = sa.InsertNextValue(fname)
        self.logger.info("read {} files".format(i))

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

        return reader.GetOutput()

    def _read_raw_image(self, progress_callback=None):
        if self.original_image_attrs is None or 'shape' not in self.original_image_attrs.keys():
            raise Exception(
                "To read a raw image, raw_image_attrs must be set.")

        isFortran = self.original_image_attrs['is_fortran']
        isBigEndian = self.original_image_attrs['is_big_endian']
        typecode = self.original_image_attrs['typecode']
        shape = tuple(self.original_image_attrs['shape'])

        if self.crop:
            reader = cilRawCroppedReader()
            reader.SetTargetZExtent(tuple(self.target_z_extent))
        else:
            reader = cilRawResampleReader()
        
        reader.SetBigEndian(isBigEndian)
        reader.SetIsFortran(isFortran)
        reader.SetTypeCodeName(typecode)
        reader.SetStoredArrayShape(shape)

        return reader
    
    def _get_hdf5_image_reader(self):

        if self.crop:
            reader = cilHDF5CroppedReader()
            reader.SetTargetExtent([0, -1, 0, -1, self.target_z_extent[0], self.target_z_extent[1]])

        else:
            reader = cilHDF5ResampleReader()

        reader.SetDatasetName(self.hdf5_dataset_name)

        return reader


    # TODO: test logger
    def _set_up_logger(self, fname):
        """Set up the logger """
        self.logger = logging.getLogger("ccpi.viewer.utils.io.ImageReader")
        self.logger.setLevel(logging.INFO)
        if fname:
            print("Will output results to: " + fname)
            handler = logging.FileHandler(fname)
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
        '''
        Constructor

        Parameters
        ----------
        file_name: os.path or string, default None
            file name to write to
        format: string, default None
            file format to write out.
            Must be one of: hdf5 #TODO
        datasets: list, default None
            list of datasets to write to the file
        attributes: list, default None
            list of dictionaries which contain the attributes
            of the dataset in datasets with the same index.           
        '''
        file_name = kwargs.get('file_name', None)
        format = kwargs.get('format', None)
        datasets = kwargs.get('datasets', None)
        attributes = kwargs.get('attributes', None)

        # can have multiple datasets
        # so we want to input list of datasets and their attributes and optionally the data
        # so we have
        # datasets = [[dataset, attributes], [dataset1, attributes1]] and they're auto written to entry1, entry2 etc.
        # if dataset entry is None we must have an attribute file_name

        # Attributes will be like:
        # info about original dataset:
        # self.original_image_attrs['shape'] = reader.GetStoredArrayShape()
        # self.original_image_attrs['spacing'] = reader.GetElementSpacing()
        # self.original_image_attrs['origin'] = reader.GetOrigin()
        # self.original_image_attrs['bit_depth'] = str(reader.GetBytesPerElement()*8)
        # self.original_image_attrs['is_big_endian'] = reader.GetBigEndian()
        # self.original_image_attrs['header_length'] = reader.GetFileHeaderLength()
        # Also 'file_name'

        # # info about new dataset:
        # self.loaded_image_attrs['spacing'] = data.GetSpacing()
        # self.loaded_image_attrs['origin'] = data.GetOrigin()
        # self.loaded_image_attrs['vtk_array_name'] = 'ImageScalars'

        # we want to then make a reader so that the viewer uses the spacing etc that has been 
        # written out to this file

        self.set_up(file_name, format, datasets, attributes)

    def set_up(self, file_name, format, datasets, attributes):
        '''
        Parameters
        ----------
        file_name: os.path or string, default None
            file name to write to
        format: string, default None
            file format to write out.
            Must be one of: hdf5 #TODO
        datasets: list, default None
            list of datasets to write to the file
        attributes: list, default None
            list of dictionaries which contain the attributes
            of the dataset in datasets with the same index.           
        '''
        for var in [file_name, format, datasets, attributes]:
            if var is None:
                raise Exception("file_name, format, dataset(s) and attribute(s), are required.")
        self.file_name = file_name
        self.format = format
        self.datasets = datasets
        self.attributes = attributes
        

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


    # def _write_hdf5(self):
    #     with h5py.File(self.file_name, 'w') as f:
            
    #         # give the file some important attributes
    #         f.attrs['file_name'] = self.file_name
    #         f.attrs['cilviewer_version'] = version
    #         f.attrs['file_time'] = str(datetime.datetime.utcnow())
    #         f.attrs['creator'] = np.string_('io.py')
    #         f.attrs['HDF5_Version'] = h5py.version.hdf5_version
    #         f.attrs['h5py_version'] = h5py.version.version
            
    #         # create the NXentry group
    #         nxentry = f.create_group('entry1/tomo_entry')
    #         nxentry.attrs['NX_class'] = 'NXentry'


    #         for i, dataset in enumerate(self.datasets):
    #             data = dataset
    #             dataset_info = self.attributes[i]
    #             entry_num = i+1
    #             dataset_name = 'entry{}/tomo_entry/data/data'.format(entry_num)

    #             vtk_array_name = dataset_info.get('vtk_array_name', 'ImageScalars')#'vtkarray')

    #             if data is not None:
    #                 print(data, vtk_array_name)
    #                 wdata = dsa.WrapDataObject(data)
    #                 array = wdata.PointData[vtk_array_name]
    #                 # Note that we flip the shape here because
    #                 # VTK's order is Fortran whereas h5py writes in
    #                 # C order. We don't want to do deep copies so we write
    #                 # with shape flipped and pretend the array is
    #                 # C order.
    #                 array = array.reshape(wdata.GetDimensions()[::-1])
    #             else:
    #                 # If we have no data then we want to save info about a dataset in another
    #                 # file, so we want to have an attribute which is called 'file_name'
    #                 if dataset_info.get("file_name") is None:
    #                     raise Exception("If no name is given for a dataset, the attributes must include the 'file_name'.")
    #                 array = None
    #             try:
    #                 if array is None:
    #                     dset = f.create_dataset(dataset_name, dataset_info['shape'] ) #, dataset_info['typecode']) # do we need?
    #                 else:
    #                     dset = f.create_dataset(dataset_name, data=array ) # , dtype= dataset_info['typecode']) # do we need?
    #             except RuntimeError:
    #                     print("Unable to save image data to {0}."
    #                         "Dataset with name {1} already exists in this file.".format(
    #                             self.file_name, dataset_name))
                

    #             for key, value in dataset_info.items():
    #                 # we want to save all the attributes except for the 
    #                 # vtk array name and the typecode
    #                 if 'vtk_array_name' not in key and 'typecode' not in key:
    #                     dset.attrs[key] = value

    #         #[0,1,2,3]

    #         #create data entry
    #         #original_data = 


    #         # # data attributes:
    #         # # original dataset will be in 'entry1/tomo_entry/data/data'
            
    #         # original_data.attrs['original_fname'] = filepath to original data
    #         # original_data.attrs['original_shape'] = shape of  original  data
    #         # original_data.attrs['original_origin'] =
    #         # original_data.attrs['original_spacing'] =

    #         # # downsampled or cropped (or both) will be in: 'entry2/tomo_entry/data/data'
    #         # modified_data.attrs['resampled'] = bool
    #         # modified_data.attrs['cropped'] = bool
    #         # modified_data.attrs['spacing'] =
    #         # modified_data.attrs['origin']=

    def _write_tiff(self):
        pass

    def _write_hdf5(self):
        writer = vortexImageWriter(file_name=self.file_name, format=self.format, datasets=self.datasets, attributes=self.attributes)
        writer.write()




class vortexImageWriter(ImageWriter):
    def __init__(self, **kwargs):
        '''
        Constructor

        Parameters
        ----------
        file_name: os.path or string, default None
            file name to write to
        format: string, default None
            file format to write out.
            Must be one of: hdf5 #TODO
        datasets: list, default None
            list of datasets to write to the file
        attributes: list, default None
            list of dictionaries which contain the attributes
            of the dataset in datasets with the same index.           
        '''

        super(vortexImageWriter, self).__init__(**kwargs)       

    def write(self):
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
                data = dataset
                dataset_info = self.attributes[i]
                entry_num = i+1
                dataset_name = 'entry{}/tomo_entry/data/data'.format(entry_num)

                vtk_array_name = dataset_info.get('vtk_array_name', 'ImageScalars')#'vtkarray')

                if data is not None:
                    print(data, vtk_array_name)
                    wdata = dsa.WrapDataObject(data)
                    array = wdata.PointData[vtk_array_name]
                    # Note that we flip the shape here because
                    # VTK's order is Fortran whereas h5py writes in
                    # C order. We don't want to do deep copies so we write
                    # with shape flipped and pretend the array is
                    # C order.
                    array = array.reshape(wdata.GetDimensions()[::-1])
                else:
                    # If we have no data then we want to save info about a dataset in another
                    # file, so we want to have an attribute which is called 'file_name'
                    if dataset_info.get("file_name") is None:
                        raise Exception("If no name is given for a dataset, the attributes must include the 'file_name'.")
                    array = None
                try:
                    if array is None:
                        dset = f.create_dataset(dataset_name, dataset_info['shape'] ) #, dataset_info['typecode']) # do we need?
                    else:
                        dset = f.create_dataset(dataset_name, data=array ) # , dtype= dataset_info['typecode']) # do we need?
                except RuntimeError:
                        print("Unable to save image data to {0}."
                            "Dataset with name {1} already exists in this file.".format(
                                self.file_name, dataset_name))
                

                for key, value in dataset_info.items():
                    # we want to save all the attributes except for the 
                    # vtk array name and the typecode
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



class vortexHDF5ImageReader(HDF5Reader):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
                                        nInputPorts=0,
                                        nOutputPorts=1,
                                        outputType='vtkImageData')

        super(vortexHDF5ImageReader, self).__init__()
        self._DatasetName = 'entry2/tomo_entry/data/data'
        print("dataset_name: ", self._DatasetName)


    def RequestData(self, request, inInfo, outInfo):
        output = super(vortexHDF5ImageReader, self)._update_output_data(outInfo)
        with h5py.File(self._FileName, 'r') as f:      
            attrs = f[self._DatasetName].attrs
            output.SetOrigin(attrs['origin'])
            output.SetSpacing(attrs['spacing'])
        return 1

    def GetOriginalDataset(self):
        # TODO
        # should this return the filename?
        # or the attributes
        # or the dataset as imagedata if present?
        pass


            

# if __name__ == "__main__":
    
    # reader = ImageReader(file_name=r"D:\lhe97136\Work\Data\24737_fd_normalised.nxs", resample=True, crop=False, log_file='log_test.log')
    # reader.read()

    # reader2 = ImageReader(file_name=r"D:\lhe97136\Work\Data\24737_fd_normalised.nxs", resample=True, crop=True, target_z_extent=[1,4], log_file='log_test_debug.log')
    # reader2.logger.setLevel(logging.DEBUG)
    # reader2.read()
    # reader = ImageReader(file_name=r"D:\lhe97136\Work\Data\24737_fd_normalised.nxs", resample=True)#)crop=True, resample=False, target_z_extent=[1, 2], resample_z=False)
    # img=reader.read()
    # print("the image is: ", img)
    # iviewer(img, img)
    # original_image_attrs = reader.get_original_attrs()
    # loaded_image_attrs = reader.get_loaded_attrs()
    # writer = ImageWriter(file_name='test_empty_dataset.hdf5', format='hdf5', datasets=[None, img], attributes=[original_image_attrs, loaded_image_attrs])
    # writer.write()
    # h5dump('test_empty_dataset.hdf5')



    # reader2 = ImageReader(file_name=r"C:\Users\lhe97136\Work\Data\24737_fd_normalised.nxs", hdf5_image_attrs={'dataset_name': 'entry2/tomo_entry/data/data'})
    # img2=reader.read()
    # original_image_attrs2 = reader.get_original_attrs()
    # loaded_image_attrs2 = reader.get_loaded_attrs()

    # print(img)
    # print(img2)
