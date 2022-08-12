import datetime
import glob
import logging
import os
import re
from functools import partial

import h5py
import numpy as np
import vtk
from ccpi.viewer.utils import Converter
from ccpi.viewer.utils.conversion import (cilHDF5CroppedReader, cilHDF5ResampleReader, cilMetaImageCroppedReader,
                                          cilMetaImageResampleReader, cilNumpyCroppedReader, cilNumpyResampleReader,
                                          cilRawCroppedReader, cilRawResampleReader, cilTIFFCroppedReader,
                                          cilTIFFResampleReader)
from ccpi.viewer.utils.error_handling import EndObserver, ErrorObserver
from ccpi.viewer.utils.hdf5_io import HDF5Reader
from ccpi.viewer.version import version
from schema import Optional, Or, Schema, SchemaError
from vtk.util import numpy_support
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase


def SaveRenderToPNG(render_window, filename):
    ''' Saves contents of a vtk render window
    to a PNG file.

    Parameters
    ----------
    render_window: vtkRenderWindow
        render window to save contents of.
    filename: str
        name of file to write PNG to.
    '''
    w2if = vtk.vtkWindowToImageFilter()
    w2if.SetInput(render_window)
    w2if.Update()

    basename = os.path.splitext(os.path.basename(filename))[0]
    # Note regex matching is different to glob matching:
    regex = '{}_([0-9]*)\.png'.format(basename)
    fname_string = '{}_{}.png'.format(basename, '[0-9]*')
    directory = os.path.dirname(filename)
    slist = []

    for el in glob.glob(os.path.join(directory, fname_string)):
        el = os.path.basename(el)
        slist.append(int(re.search(regex, el).group(1)))

    if len(slist) == 0:
        number = 0
    else:
        number = max(slist) + 1

    saveFilename = '{}_{:04d}.png'.format(os.path.join(directory, basename), number)

    writer = vtk.vtkPNGWriter()
    writer.SetFileName(saveFilename)
    writer.SetInputConnection(w2if.GetOutputPort())
    writer.Write()


# TODO:
# supporting tiffs
# write out other filetypes


class ImageReader(object):
    '''
    Generic reader for reading to vtkImageData
    Currently reads: HDF5, MetaImage, Numpy, Raw, TIFF stacks
    Supports resampling OR cropping the dataset whilst
    reading.
    Currently doesn't support both cropping and resampling
    If set both to true then it resamples and doesn't crop
    '''

    def __init__(self,
                 file_name=None,
                 resample=True,
                 target_size=512**3,
                 crop=False,
                 target_z_extent=None,
                 resample_z=False,
                 raw_image_attrs=None,
                 hdf5_dataset_name="entry1/tomo_entry/data/data",
                 log_file=None):
        '''
        Constructor

        Parameters
        ----------
        file_name: os.path or string, default None
            file name to read
            In case of TIFF files, either the directory to the TIFF files, or the path to one such file is needed.
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

        if file_name is None:
            raise Exception('Path to file is required.')

        if not (os.path.isfile(file_name) or os.path.isdir(file_name)):
            raise Exception('Path\n {}\n does not exist.'.format(file_name))

        self._OriginalImageAttrs = {}

        self.SetFileName(file_name)
        self.SetResample(resample)
        self.SetTargetSize(target_size)
        self.SetCrop(crop)
        self.SetTargetZExtent(target_z_extent)
        self.SetResampleZ(resample_z)
        self.SetHDF5DatasetName(hdf5_dataset_name)
        self.SetRawImageAttributes(raw_image_attrs)
        self.SetLogFileName(log_file)

    def SetFileName(self, file_name):
        '''
        Parameters
        ----------
        file_name: os.path or string, default None
            file name to read
        '''
        self._FileName = file_name

    def SetResample(self, resample):
        '''
        Parameters
        ----------
        resample: bool, default True
            whether to resample
        '''
        self._Resample = resample

    def SetTargetSize(self, target_size):
        '''
        Parameters
        ----------
        target_size: int, default 512**3
            target size after downsampling
        '''

        self._TargetSize = target_size

    def SetCrop(self, crop):
        '''
        Parameters
        ----------
        crop: bool, default False
            whether to crop
        '''
        self._Crop = crop

    def SetTargetZExtent(self, target_z_extent):
        '''
        Parameters
        ----------
        target_z_extent: list [,], default None
            desired extent after cropping on z axis
            '''
        self._TargetZExtent = target_z_extent

    def SetResampleZ(self, resample_z):
        '''
        Parameters
        ----------
        resample_z: bool, default True
            whether to resample on the z axis. E.g. in the case we have
            acquisition data, the projections would be on the z axis, so
            we would not want to resample in that direction.
        '''
        self._ResampleZ = resample_z

    def SetHDF5DatasetName(self, hdf5_dataset_name):
        '''
        Parameters
        ----------
        hdf5_dataset_name: string, default "entry1/tomo_entry/data/data"
            Name of the hdf5 dataset to be read, if file format is hdf5
        '''
        self._HDF5DatasetName = hdf5_dataset_name

    def SetLogFileName(self, log_file):
        '''
        Parameters
        ----------
        log_file: str, optional, default None
            log verbose output to file of this name            
        '''
        self._SetUpLogger(log_file)

    def SetRawImageAttributes(self, raw_image_attrs):
        if raw_image_attrs is not None and raw_image_attrs != {}:
            try:
                raw_attrs = self._ValidateRawAttrs(raw_image_attrs)
                self._OriginalImageAttrs = raw_attrs
            except SchemaError as e:
                raise ValueError("Error: Raw image attributes were not input correctly: ", e)

    def Read(self, *args, **kwargs):
        ''' reads self._FileName
            returns vtkImageData'''
        # identifies file type
        # uses appropriate reader based on file type and cropping or resampling

        if self._Crop:
            if self._TargetZExtent is None:
                raise TypeError("If crop is set to True, target_z_extent must be set.")
            if self._Resample:
                self.logger.warning(
                    "Both cropping and resampling is not yet implemented. Image will just be cropped and not resampled."
                )
                self._Resample = False

        self._LoadedImageAttrs = {'resampled': self._Resample, 'cropped': self._Crop}

        self.logger.info("reading: {}".format(self._FileName))

        progress_callback = kwargs.get('progress_callback')

        reader = self._GetReader(progress_callback)
        reader.Update()
        data = reader.GetOutput()

        self._UpdateLoadedImageAttrs(reader, data)

        self._UpdateOriginalImageAttrs(reader)

        return data

    def GetOriginalImageAttrs(self):
        return self._OriginalImageAttrs

    def GetLoadedImageAttrs(self):
        return self._LoadedImageAttrs

    def _ValidateRawAttrs(self, raw_image_attrs):
        if raw_image_attrs is None:
            return
        raw_attrs = raw_image_attrs.copy()
        raw_attrs_schema = Schema({
            'shape': Or(list, np.ndarray, tuple),
            'is_fortran': bool,
            'is_big_endian': bool,
            'typecode': str
        })
        raw_attrs_schema.validate(raw_attrs)
        return raw_attrs

    def _GetReader(self, progress_callback=None):
        '''
        Returns an appropriate reader for the image file provided.
        The appropriate reader is decided by matching the extension of the file to be read, which can be:
        - mha, mhd for METAIO files
        - npy for numpy file format
        - raw for binary blobs
        - nxs, h5, or hdf5 for HDF5 files
        - tiff or tif for TIFF stacks.
        No actual check of the file format is performed.
        '''
        if os.path.isfile(self._FileName):
            file_extension = os.path.splitext(self._FileName)[1]

            if file_extension in ['.mha', '.mhd']:
                reader = self._GetMetaImageReader()

            elif file_extension in ['.npy']:
                reader = self._GetNumpyImageReader()

            elif file_extension in ['.raw']:
                reader = self._GetRawImageReader()

            elif file_extension in ['.nxs', '.h5', '.hdf5']:
                reader = self._GetHDF5ImageReader()
                self._OriginalImageAttrs['dataset_name'] = self._HDF5DatasetName

            elif file_extension in ['.tif', '.tiff']:
                image_files = glob.glob(os.path.join(os.path.dirname(self._FileName), '*{}'.format(file_extension)))
                if len(image_files) == 0:
                    raise Exception('No tiff files were found in: {}'.format(os.path.dirname(self._FileName)))
                reader = self._GetTiffImageReader()
                reader.SetFileName(image_files)

            else:
                raise Exception('File format is not supported. Accepted formats include: .mhd, .mha, .npy, .tif, .raw')
        else:  # If we are given a folder, not a file, look for tiff files and try to read them
            image_files = glob.glob(os.path.join(self._FileName, '*.tif')) + glob.glob(
                os.path.join(self._FileName, '*.tiff'))
            if len(image_files) == 0:
                raise Exception('No tiff files were found in: {}'.format(self._FileName))
            reader = self._GetTiffImageReader()
            reader.SetFileName(image_files)
            file_extension = '.tiff'

        if file_extension not in ['.tif', '.tiff']:
            # currently the tiff reader doesn't take these inputs:
            reader.SetFileName(self._FileName)

        # setting SetIsAcquisitionData determines whether to crop on Z:
        reader.SetIsAcquisitionData(not self._ResampleZ)

        if not self._Crop:
            if self._Resample:
                target_size = self._TargetSize
            else:
                # forced use of resample reader in the case that we
                # don't want to crop or resample,
                # but the large target size means we don't resample
                target_size = 1e12
            reader.SetTargetSize(int(target_size))

        # Add observers:
        reader.AddObserver(vtk.vtkCommand.ProgressEvent,
                           partial(self._ReportProgress, progress_callback=progress_callback))

        # Prints the error if an error occurs in the reader.
        # Otherwise this wouldn't print at all.
        error_obs = ErrorObserver(callback_fn=print)
        reader.AddObserver(vtk.vtkCommand.ErrorEvent, error_obs)
        # Could add end observer so that we don't continue to do anything
        # else if an error does occur in reader?

        return reader

    def _GetMetaImageReader(self, progress_callback=None):
        if self._Crop:
            reader = cilMetaImageCroppedReader()
            reader.SetTargetZExtent(tuple(self._TargetZExtent))
        else:
            reader = cilMetaImageResampleReader()
        return reader

    def _GetNumpyImageReader(self, progress_callback=None):
        if self._Crop:
            reader = cilNumpyCroppedReader()
            reader.SetTargetZExtent(tuple(self._TargetZExtent))
        else:
            reader = cilNumpyResampleReader()

        return reader

    def _GetTiffImageReader(self, progress_callback=None):
        if self._Crop:
            reader = cilTIFFCroppedReader()
            reader.SetTargetZExtent(tuple(self._TargetZExtent))
        else:
            reader = cilTIFFResampleReader()
        return reader

    def _GetRawImageReader(self):
        if self._OriginalImageAttrs is None or 'shape' not in self._OriginalImageAttrs.keys():
            raise Exception("To read a raw image, raw_image_attrs must be set.")

        isFortran = self._OriginalImageAttrs['is_fortran']
        isBigEndian = self._OriginalImageAttrs['is_big_endian']
        typecode = self._OriginalImageAttrs['typecode']
        shape = tuple(self._OriginalImageAttrs['shape'])

        if self._Crop:
            reader = cilRawCroppedReader()
            reader.SetTargetZExtent(tuple(self._TargetZExtent))
        else:
            reader = cilRawResampleReader()

        reader.SetBigEndian(isBigEndian)
        reader.SetIsFortran(isFortran)
        reader.SetTypeCodeName(typecode)
        reader.SetStoredArrayShape(shape)

        return reader

    def _GetHDF5ImageReader(self):
        if self._Crop:
            reader = cilHDF5CroppedReader()
            reader.SetTargetExtent([0, -1, 0, -1, self._TargetZExtent[0], self._TargetZExtent[1]])

        else:
            reader = cilHDF5ResampleReader()

        reader.SetDatasetName(self._HDF5DatasetName)

        return reader

    def _SetUpLogger(self, fname=None, log_level=logging.INFO):
        """Set up the logger """
        self.logger = logging.getLogger("ccpi.viewer.utils.io.ImageReader")
        self.logger.setLevel(log_level)
        if fname is not None:
            handler = logging.FileHandler(fname)
            self.logger.addHandler(handler)

    def _ReportProgress(self, caller, event, progress_callback=None):
        ''' This emits the progress as a value between 1 and 100,
        and writes to a log file.
        If a Qt progress_callback has been passed, this allows progress to be kept track
        of if the reading is run in a Worker thread.'''
        progress_value = caller.GetProgress() * 100
        progress = "{:.1f}%".format(progress_value)
        self.logger.info(progress)

        if progress_callback is not None:
            progress_callback.emit(int(progress_value))

    def _UpdateLoadedImageAttrs(self, reader, data):
        # Make sure whether we did resample or not:
        if self._Resample:
            original_image_size = reader.GetStoredArrayShape()[0] * reader.GetStoredArrayShape(
            )[1] * reader.GetStoredArrayShape()[2]
            resampled_image_size = reader.GetTargetSize()
            if original_image_size <= resampled_image_size:
                self._LoadedImageAttrs['resampled'] = False
            else:
                self._LoadedImageAttrs['resampled'] = True
        # info about new dataset:
        self._LoadedImageAttrs['spacing'] = data.GetSpacing()
        self._LoadedImageAttrs['origin'] = data.GetOrigin()
        if self._Resample:
            self._LoadedImageAttrs['resample_z'] = self._ResampleZ

    def _UpdateOriginalImageAttrs(self, reader):
        self._OriginalImageAttrs['shape'] = reader.GetStoredArrayShape()
        self._OriginalImageAttrs['spacing'] = reader.GetElementSpacing()
        self._OriginalImageAttrs['origin'] = reader.GetOrigin()
        self._OriginalImageAttrs['bit_depth'] = str(reader.GetBytesPerElement() * 8)
        self._OriginalImageAttrs['is_big_endian'] = reader.GetBigEndian()
        self._OriginalImageAttrs['header_length'] = reader.GetFileHeaderLength()
        self._OriginalImageAttrs['file_name'] = self._FileName
        self._OriginalImageAttrs['resampled'] = False
        self._OriginalImageAttrs['cropped'] = False


class ImageWriterInterface(object):
    '''
    Base class with methods for setting and getting information about modified
    (i.e. resampled or cropped) image data to write to a file.
    '''

    def __init__(self):
        self._FileName = None
        self._FileFormat = None
        self._OriginalDataset = None
        self._ChildDatasets = []
        self._OriginalDatasetAttributes = None
        self._ChildDatasetsAttributes = []
        self._Chunking = True
        self._ChunkShape = None
        self._HDF5Compression = None

    def SetFileName(self, value):
        '''
        Set the file name or path where to write the image data

        Parameters
        -----------
        value: (str)
            file name or path
        '''
        self._FileName = value

    def GetFileName(self):
        ''' The file name or path where to write the image data '''
        return self._FileName

    def SetFileFormat(self, value):
        '''
        Parameters
        -----------
        value: (str)
            file format
            must be one of: hdf5, nexus, mha
        '''
        self._FileFormat = value

    def GetFileFormat(self):
        return self._FileFormat

    def SetOriginalDataset(self, original_dataset, attributes):
        '''Parameters
        -----------
        original_dataset: vtkImageData or None
            original dataset, or None if this won't be saved to the file
        attributes: dict
            dictionary containing attributes of original dataset
        '''
        if not isinstance(original_dataset, vtk.vtkImageData) and not (original_dataset is None):
            raise Exception("'original_dataset' must be vtk.vtkImageData or None")

        self._validate_original_dataset_attributes(original_dataset, attributes)
        self._OriginalDataset = original_dataset
        self._OriginalDatasetAttributes = attributes

    def _validate_original_dataset_attributes(self, original_dataset, attributes):
        if not isinstance(attributes, dict):
            raise Exception("'attributes' must be a dictionary.")
        if original_dataset is None:
            # must have shape and filename set
            if attributes.get("file_name") is None or attributes.get("shape") is None:
                raise Exception(
                    "If no name is given for a dataset, the attributes must include the 'file_name' and the 'shape'.")

        original_attributes_schema = Schema({
            Optional('file_name'): str,
            Optional('shape'): Or(list, tuple),
            'resampled': False,
            'cropped': False,
            Optional(str): object  # allow any other keys and values
        })

        original_attributes_schema.validate(attributes)

    def AddChildDataset(self, child_dataset, attributes=None):
        if not isinstance(child_dataset, vtk.vtkImageData):
            raise Exception("child_dataset must be vtk.vtkImageData")
        # check type is vtkImageData
        self._ValidateChildDatasetAttributes(child_dataset, attributes)
        self._ChildDatasets.append(child_dataset)
        self._ChildDatasetsAttributes.append(attributes)

    def _ValidateChildDatasetAttributes(self, child_dataset, attributes):
        if not isinstance(attributes, dict) and not (attributes is None):
            raise Exception("'attributes' must be a dictionary, or unset (i.e. None)")

    def SetChunking(self, chunking):
        '''
        Parameters
        ----------
        chunking: bool, default: True in case of HDF5 file,
                  otherwise False
            Whether to write to the file in chunks.
        '''
        self._Chunking = chunking

    def SetChunkShape(self, chunk_shape):
        '''
        Parameters
        ----------
        chunk_shape: tuple, default: one slice on the z axis
            If SetChunking() has been set to True, this will be
            the size of a chunk written to the file.
        '''
        self._ChunkShape = chunk_shape

    def SetHDF5Compression(self, compression):
        '''
        Parameters
        ----------
        compression: list, default None
            This is a list of compression settings when writing to HDF5
            First element: str
                The type of hdf5 compression to use.
                Must be one of: None, 'gzip', or 'lzf'
            Second element:
                Options for the compression filter. For details, see:
                https://docs.h5py.org/en/stable/high/dataset.html?highlight=compression_opts#dataset-compression
            Third element: bool
                Whether to shuffle the data i.e. rearrange the bytes in
                a chunk, which may improve the compression ratio
        '''
        self._HDF5Compression = compression


class ImageWriter(ImageWriterInterface):
    '''
    Writer for writing out a modified i.e. resampled or cropped dataset.
    Currently supports writing to HDF5 and metaimage.
    
    In the case of HDF5:
    Expects to be writing an original dataset or attributes of the original dataset,
    plus one or more 'child' versions of the dataset which have been resampled and/or cropped.
    This can be done if the file format is set to hdf5 or nxs.
    If an image has been downsampled/cropped using the ImageReader class, then the attributes 
    obtained with: reader.get_original_image_attributes() and reader.get_loaded_image_attributes()
    will be in the correct format for this writer.
    
    Example of writing to HDF5:
    writer = ImageWriter()
    writer.SetFileName('resampled_image')
    writer.SetFileFormat('hdf5')
    writer.SetOriginalDataset(None, 
        {'file_name': 'image.nxs', 'shape': [500, 600, 600], 'resampled': False, 'cropped': False})
    writer.AddChildDataset(downsampled_image,  
        {'origin': [0.5, 0.5, 0.5], 'spacing': [2, 2, 2], 'resampled': True, 'resampled_z': False, 'cropped': False})
    writer.Write()

    Alternatively, to just write a downsampled/cropped dataset to a metaimage file with no extra attributes.
    Remember the metaimage writer already automatically will save the spacing and origin of the vtkImageData
    so there is no need to set this as extra attributes.
    Example of writing to MHA:
    writer = ImageWriter()
    writer.SetFileName('resampled_image')
    writer.SetFileFormat('mha')
    writer.AddChildDataset(downsampled_image)
    writer.Write()
    With mha this means we lose the information about the original dataset before it was downsampled/cropped

    '''

    def __init__(self):
        super(ImageWriter, self).__init__()

    def Write(self):
        # check file ext
        writer = self._GetWriter()
        writer.Write()

    def _GetWriter(self):
        file_name = os.path.splitext(self._FileName)[0]

        if self._FileFormat in ['nxs', 'h5', 'hdf5', '']:
            self._FileName = file_name + '.hdf5'
            writer = self._GetHDF5Writer()

        elif self._FileFormat in ['mha']:
            self._FileName = file_name + '.mha'
            writer = self._GetMetaImageWriter()

        else:
            raise Exception("File format is not supported. Supported types include hdf5/nexus.")

        writer.SetFileName(self._FileName)
        return writer

    def _GetHDF5Writer(self):
        writer = cilviewerHDF5Writer()
        writer.SetOriginalDataset(None, self._OriginalDatasetAttributes)
        writer.SetChunking(self._Chunking)
        writer.SetChunkShape(self._ChunkShape)
        writer.SetHDF5Compression(self._HDF5Compression)
        for i in range(0, len(self._ChildDatasets)):
            writer.AddChildDataset(self._ChildDatasets[i], self._ChildDatasetsAttributes[i])
        return writer

    def _GetMetaImageWriter(self):
        writer = vtk.vtkMetaImageWriter()
        writer.SetInputData(self._ChildDatasets[0])
        return writer


class cilviewerHDF5Writer(ImageWriterInterface):
    '''
    Expects to be writing an original dataset or attributes of the original dataset,
    plus one or more 'child' versions of the dataset which have been resampled and/or cropped.
    '''

    def __init__(self):
        super(cilviewerHDF5Writer, self).__init__()

    def _ValidateChildDatasetAttributes(self, child_dataset, attributes):
        if not isinstance(attributes, dict):
            raise Exception("'attributes must be a dictionary.")
        # check origin and spacing are set
        # check resampling and cropping are set
        child_attributes_schema = Schema({
            'resampled': bool,
            'cropped': bool,
            'spacing': Or(list, tuple),
            'origin': Or(list, tuple),
            Optional('resample_z'): bool,
            Optional(str): object  # allow any other keys and values
        })
        child_attributes_schema.validate(attributes)

    def Write(self):
        for var in [self._FileName, self._OriginalDatasetAttributes]:
            if var is None:
                raise Exception("file_name, dataset(/s) and attribute(/s), are required.")
        for var in [self._ChildDatasets, self._ChildDatasetsAttributes]:
            if var is []:
                raise Exception("child dataset(/s) and attribute(/s), are required.")

        with h5py.File(self._FileName, 'w') as f:

            # give the file some important attributes
            f.attrs['file_name'] = self._FileName
            f.attrs['viewer_version'] = version
            f.attrs['file_time'] = str(datetime.datetime.utcnow())
            f.attrs['creator'] = np.string_('io.py')
            f.attrs['HDF5_Version'] = h5py.version.hdf5_version
            f.attrs['h5py_version'] = h5py.version.version

            # create the NXentry group
            nxentry = f.create_group('entry1/tomo_entry')
            nxentry.attrs['NX_class'] = 'NXentry'

            datasets = [self._OriginalDataset]
            datasets += self._ChildDatasets

            attributes = [self._OriginalDatasetAttributes]
            attributes += self._ChildDatasetsAttributes

            for i, dataset in enumerate(datasets):
                data = dataset
                dataset_info = attributes[i]
                entry_num = i + 1
                dataset_name = 'entry{}/tomo_entry/data/data'.format(entry_num)

                if data is not None:
                    # The function imgdata.GetPointData().GetScalars() returns a pointer to a
                    # vtk<TYPE>Array where the data is stored as X-Y-Z.
                    array = numpy_support.vtk_to_numpy(data.GetPointData().GetScalars())

                    # Note that we flip the shape here because
                    # VTK's order is Fortran whereas h5py writes in
                    # C order. We don't want to do deep copies so we write
                    # with shape flipped and pretend the array is
                    # C order.
                    array = array.reshape(data.GetDimensions()[::-1])
                else:
                    array = None
                try:
                    if array is None:
                        dset = f.create_dataset(dataset_name, dataset_info['shape'])
                    else:
                        if self._Chunking:
                            if self._ChunkShape is None:
                                # If Chunking has been selected but a shape has not,
                                # by default use a slice as the chunk
                                slice_shape = list(array.shape)
                                slice_shape[0] = 1
                                self._ChunkShape = tuple(slice_shape)
                            if self._HDF5Compression is None or self._HDF5Compression[0] is None:
                                dset = f.create_dataset(dataset_name, data=array, chunks=self._ChunkShape)
                            elif self._HDF5Compression[0] == 'gzip':
                                dset = f.create_dataset(dataset_name,
                                                        data=array,
                                                        chunks=self._ChunkShape,
                                                        compression=self._HDF5Compression[0],
                                                        compression_opts=self._HDF5Compression[1],
                                                        shuffle=self._HDF5Compression[2])
                            elif self._HDF5Compression[0] == 'lzf':
                                dset = f.create_dataset(dataset_name,
                                                        data=array,
                                                        chunks=self._ChunkShape,
                                                        compression=self._HDF5Compression[0],
                                                        shuffle=self._HDF5Compression[2])
                        else:
                            dset = f.create_dataset(dataset_name, data=array)

                except RuntimeError:
                    print("Unable to save image data to {0}."
                          "Dataset with name {1} already exists in this file.".format(self._FileName, dataset_name))

                if entry_num != 1:
                    dset.attrs['original_dataset'] = 'entry1/tomo_entry/data/data'

                for key, value in dataset_info.items():
                    dset.attrs[key] = value


class cilviewerHDF5Reader(HDF5Reader):
    '''
    Expects to be reading a file where:
    entry1 contains an original dataset or attributes of the original dataset
    The following entries contain:
    one or more 'child' versions of the dataset which have been resampled and/or cropped.
    It is one of these 'child' versions that we are interested in reading for displaying in the viewer.
    The user must specify which they would like if there is more than one. By default entry2 is read.
    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1, outputType='vtkImageData')

        super(cilviewerHDF5Reader, self).__init__()
        self._DatasetEntryNumber = 2
        self._DatasetName = 'entry{}/tomo_entry/data/data'.format(self._DatasetEntryNumber)

    def SetDatasetEntryNumber(self, num):
        '''
        The entry number that the dataset will be read from.
        By default this is set to 2 which means the dataset read is:
        'entry2/tomo_entry/data/data'
        entry numbers:
        1 - should contain the attributes of the unmodified dataset
        2 - should contain a downsampled/cropped version 
        3+ - if present, should contain another downsampled/cropped version 
        '''
        dataset_name = 'entry{}/tomo_entry/data/data'.format(num)
        if self._FileName is not None:
            with h5py.File(self._FileName, 'r') as f:
                if not (dataset_name in f):
                    raise Exception("No dataset named {} exists in {}.".format(dataset_name, self._FileName))
        self._DatasetEntryNumber = num
        self._DatasetName = dataset_name

    def GetDatasetEntryNumber(self):
        '''
        The entry number that the dataset will be read from.
        By default this is set to 2 which means the dataset read is:
        'entry2/tomo_entry/data/data'
        entry numbers:
        1 - should contain the attributes of the unmodified dataset
        2 - should contain a downsampled/cropped version 
        3+ - if present, should contain another downsampled/cropped version 
        '''
        return self._DatasetEntryNumber

    def SetDatasetName(self, lname):
        '''
        It is easier to use SetDatasetEntryNumber,
        but you may still set the name instead if you
        wish.
        '''
        super(cilviewerHDF5Reader, self).SetDatasetName(lname)
        re_str = '^entry([0-9]*)'
        try:
            self._DatasetEntryNumber = re.search(re_str, str).group(1)
        except AttributeError:
            # This means no match found so naming convention of dataset is
            # not as we expect, so we can't assign a dataset entry number.
            self._DatasetEntryNumber = None

    def RequestData(self, request, inInfo, outInfo):
        output = super(cilviewerHDF5Reader, self)._update_output_data(outInfo)
        with h5py.File(self._FileName, 'r') as f:
            attrs = f[self._DatasetName].attrs
            # TODO check on the errors if these attributes haven't been found:
            output.SetOrigin(attrs['origin'])
            output.SetSpacing(attrs['spacing'])
        return 1
