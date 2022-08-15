import os
import unittest

import h5py
import numpy as np
import vtk
from ccpi.viewer.utils.conversion import Converter
from ccpi.viewer.utils.io import ImageReader, cilviewerHDF5Writer, cilviewerHDF5Reader


def calculate_target_downsample_shape(max_size, total_size, shape, acq=False):
    if not acq:
        xy_axes_magnification = np.power(max_size / total_size, 1 / 3)
        slice_per_chunk = int(1 / xy_axes_magnification)
    else:
        slice_per_chunk = 1
        xy_axes_magnification = np.power(max_size / total_size, 1 / 2)
    num_chunks = 1 + len([i for i in range(slice_per_chunk, shape[2], slice_per_chunk)])

    target_image_shape = (int(xy_axes_magnification * shape[0]), int(xy_axes_magnification * shape[1]), num_chunks)
    return target_image_shape


# TODO:
# First, focus on resampling and writing out to HDF5
# for this we need:
# test image attributes given by reader
# test writing out a file


class TestImageReaderAndWriter(unittest.TestCase):

    def setUp(self):
        # Generate random 3D array:
        bits = 16
        self.bytes_per_element = int(bits / 8)
        self.input_3D_array = np.random.randint(10, size=(5, 10, 6), dtype=eval(f"np.uint{bits}"))
        # write to HDF5: -----------
        self.hdf5_filename_3D = 'test_3D_data.h5'
        with h5py.File(self.hdf5_filename_3D, 'w') as f:
            f.create_dataset('ImageData', data=self.input_3D_array)
        # write to NUMPY: ----------
        self.numpy_filename_3D = 'test_3D_data.npy'
        np.save(self.numpy_filename_3D, self.input_3D_array)
        # write to MHA: --------------
        self.mha_filename_3D = 'test_3D_data_1.mha'
        vtkimage = Converter.numpy2vtkImage(self.input_3D_array)
        writer = vtk.vtkMetaImageWriter()
        writer.SetInputData(vtkimage)
        writer.SetCompression(0)
        writer.SetFileName(self.mha_filename_3D)
        writer.Write()
        # write to raw: -------------
        bytes_3D_array = bytes(self.input_3D_array)
        self.raw_filename_3D = 'test_3D_data.raw'
        with open(self.raw_filename_3D, 'wb') as f:
            f.write(bytes_3D_array)
        self.raw_image_attrs = {
            'shape': np.shape(self.input_3D_array),
            'is_fortran': False,
            'is_big_endian': False,
            'typecode': str(self.input_3D_array.dtype)
        }

        # Create TIFF Files
        fnames = []
        arr = self.input_3D_array
        self.tiff_dirname = 'tiff_files'
        if not os.path.exists('tiff_files'):
            os.mkdir(self.tiff_dirname)
        from PIL import Image
        for i in range(arr.shape[0]):
            fname = 'tiff_files/tiff_test_file_{:03d}.tiff'.format(i)
            fnames.append(os.path.abspath(fname))
            # Using vtk the Y axis gets reversed
            # vtk_image = Converter.numpy2vtkImage(np.expand_dims(arr[i,:,:], axis=0))
            # twriter.SetFileName(fnames[-1])
            # twriter.SetInputData(vtk_image)
            # twriter.Write()
            im = Image.fromarray(arr[i])
            im.save(fnames[-1])

        self.tiff_fnames = fnames

    def _test_read_full_size_data(self, reader):
        array_image_data = reader.Read()
        read_array = Converter.vtk2numpy(array_image_data)
        np.testing.assert_array_equal(self.input_3D_array, read_array)

    def _test_resampling_not_acq_data(self, reader, target_size):
        image = reader.Read()
        extent = image.GetExtent()
        resulting_shape = (extent[1] + 1, (extent[3] + 1), (extent[5] + 1))
        og_shape = np.shape(self.input_3D_array)
        og_shape = (og_shape[2], og_shape[1], og_shape[0])
        og_size = og_shape[0] * og_shape[1] * og_shape[2] * self.bytes_per_element
        expected_shape = calculate_target_downsample_shape(target_size, og_size, og_shape)
        self.assertEqual(resulting_shape, expected_shape)

    def _test_resample_size_bigger_than_image_size(self, reader):
        image = reader.Read()
        extent = image.GetExtent()
        og_shape = np.shape(self.input_3D_array)
        og_shape = (og_shape[2], og_shape[1], og_shape[0])
        expected_shape = og_shape
        resulting_shape = (extent[1] + 1, (extent[3] + 1), (extent[5] + 1))
        self.assertEqual(resulting_shape, expected_shape)
        resulting_array = Converter.vtk2numpy(image)
        np.testing.assert_array_equal(self.input_3D_array, resulting_array)

    def _test_resampling_acq_data(self, reader, target_size):
        og_shape = np.shape(self.input_3D_array)
        og_shape = (og_shape[2], og_shape[1], og_shape[0])
        og_size = og_shape[0] * og_shape[1] * og_shape[2] * self.bytes_per_element
        image = reader.Read()
        extent = image.GetExtent()
        shape_not_acquisition = calculate_target_downsample_shape(target_size, og_size, og_shape, acq=True)
        expected_size = shape_not_acquisition[0] * \
            shape_not_acquisition[1]*shape_not_acquisition[2]
        resulting_shape = (extent[1] + 1, (extent[3] + 1), (extent[5] + 1))
        resulting_size = resulting_shape[0] * \
            resulting_shape[1]*resulting_shape[2]
        # angle (z direction) is first index in numpy array, and in cil
        # but it is the last in vtk.
        resulting_z_shape = extent[5] + 1
        og_z_shape = np.shape(self.input_3D_array)[0]
        self.assertEqual(resulting_size, expected_size)
        self.assertEqual(resulting_z_shape, og_z_shape)

    def test_read(self):
        '''Test reading each format without resampling or cropping'''
        readers = {}
        readers['hdf5'] = ImageReader(file_name=self.hdf5_filename_3D, resample=False, hdf5_dataset_name="ImageData")
        readers['numpy'] = ImageReader(file_name=self.numpy_filename_3D, resample=False)
        readers['mha'] = ImageReader(file_name=self.mha_filename_3D, resample=False)
        readers['raw'] = ImageReader(file_name=self.raw_filename_3D,
                                     resample=False,
                                     raw_image_attrs=self.raw_image_attrs)
        readers['tiff_file'] = ImageReader(file_name=self.tiff_fnames[0], resample=False)
        readers['tiff_dir'] = ImageReader(file_name=self.tiff_dirname, resample=False)

        for i, reader in enumerate(readers.values()):
            with self.subTest(reader_name=list(readers.keys())[i]):
                self._test_read_full_size_data(reader)

    def test_read_resample(self):

        og_shape = np.shape(self.input_3D_array)
        og_shape = (og_shape[2], og_shape[1], og_shape[0])
        og_size = og_shape[0] * og_shape[1] * og_shape[2]

        # Tests image with correct target size is generated by resample reader:
        target_size = 100
        readerhdf5 = ImageReader(file_name=self.hdf5_filename_3D,
                                 target_size=target_size,
                                 resample_z=True,
                                 hdf5_dataset_name="ImageData")
        self._test_resampling_not_acq_data(readerhdf5, target_size)
        readernpy = ImageReader(file_name=self.numpy_filename_3D, target_size=target_size, resample_z=True)
        self._test_resampling_not_acq_data(readernpy, target_size)
        readermhd = ImageReader(file_name=self.mha_filename_3D, target_size=target_size, resample_z=True)
        self._test_resampling_not_acq_data(readermhd, target_size)
        readerraw = ImageReader(file_name=self.raw_filename_3D,
                                target_size=target_size,
                                resample_z=True,
                                raw_image_attrs=self.raw_image_attrs)
        self._test_resampling_not_acq_data(readerraw, target_size)
        readertiff = ImageReader(file_name=self.tiff_dirname, target_size=target_size, resample_z=True)
        self._test_resampling_not_acq_data(readertiff, target_size)

        # Now test if we get the correct z extent if we set that we
        # have acquisition data
        readerhdf5 = ImageReader(file_name=self.hdf5_filename_3D,
                                 target_size=target_size,
                                 resample_z=False,
                                 hdf5_dataset_name="ImageData")
        self._test_resampling_acq_data(readerhdf5, target_size)
        readernpy = ImageReader(file_name=self.numpy_filename_3D, target_size=target_size, resample_z=False)
        self._test_resampling_acq_data(readernpy, target_size)
        readermhd = ImageReader(file_name=self.mha_filename_3D, target_size=target_size, resample_z=False)
        self._test_resampling_acq_data(readermhd, target_size)
        readerraw = ImageReader(file_name=self.raw_filename_3D,
                                target_size=target_size,
                                resample_z=False,
                                raw_image_attrs=self.raw_image_attrs)
        self._test_resampling_acq_data(readerraw, target_size)
        readertiff = ImageReader(file_name=self.tiff_fnames[0], target_size=target_size, resample_z=False)
        self._test_resampling_acq_data(readertiff, target_size)

        # # Now test if we get the full image extent if our
        # # target size is larger than the size of the image:
        target_size = og_size * 2
        readerhdf5 = ImageReader(file_name=self.hdf5_filename_3D,
                                 target_size=target_size,
                                 hdf5_dataset_name="ImageData")
        self._test_resample_size_bigger_than_image_size(readerhdf5)
        readernpy = ImageReader(file_name=self.numpy_filename_3D, target_size=target_size)
        self._test_resample_size_bigger_than_image_size(readernpy)
        readermhd = ImageReader(file_name=self.mha_filename_3D, target_size=target_size)
        self._test_resample_size_bigger_than_image_size(readermhd)
        readerraw = ImageReader(file_name=self.raw_filename_3D,
                                target_size=target_size,
                                raw_image_attrs=self.raw_image_attrs)
        self._test_resample_size_bigger_than_image_size(readerraw)
        readertiff = ImageReader(file_name=self.tiff_dirname, target_size=target_size)
        self._test_resample_size_bigger_than_image_size(readertiff)

    def test_read_cropped(self):
        # Test cropping the extent of a dataset
        cropped_array = self.input_3D_array[1:2, :, :]

        # HDF5: ------------------------------------------------------------------------------------------
        reader = ImageReader(file_name=self.hdf5_filename_3D,
                             crop=True,
                             resample=False,
                             target_z_extent=[1, 1],
                             hdf5_dataset_name="ImageData")

        # NOTE: the extent is in vtk so is in fortran order, whereas
        # above we had the np array in C-order so x and y cropping swapped
        array_image_data = reader.Read()
        read_cropped_array_hdf5 = Converter.vtk2numpy(array_image_data)
        np.testing.assert_array_equal(cropped_array, read_cropped_array_hdf5)

        # NUMPY: --------------------------------------------------------------
        reader = ImageReader(file_name=self.numpy_filename_3D, crop=True, resample=False, target_z_extent=[1, 1])
        array_image_data = reader.Read()
        read_cropped_array = Converter.vtk2numpy(array_image_data)
        np.testing.assert_array_equal(cropped_array, read_cropped_array)

        # METAIMAGE: -----------------------------------------------------------------
        reader = ImageReader(file_name=self.mha_filename_3D, crop=True, resample=False, target_z_extent=[1, 1])
        array_image_data = reader.Read()
        read_cropped_array = Converter.vtk2numpy(array_image_data)
        np.testing.assert_array_equal(cropped_array, read_cropped_array)

        # RAW: ----------------------------------------------------------------------
        reader = ImageReader(file_name=self.raw_filename_3D,
                             crop=True,
                             resample=False,
                             target_z_extent=[1, 1],
                             raw_image_attrs=self.raw_image_attrs)
        array_image_data = reader.Read()
        read_cropped_array = Converter.vtk2numpy(array_image_data)
        np.testing.assert_array_equal(cropped_array, read_cropped_array)

        # TIFF: ------------------------------------------------------------------------
        reader = ImageReader(file_name=self.tiff_fnames[0], crop=True, resample=False, target_z_extent=[1, 1])
        array_image_data = reader.Read()
        read_cropped_array = Converter.vtk2numpy(array_image_data)
        np.testing.assert_array_equal(cropped_array, read_cropped_array)

    def test_write_read_hdf5(self):
        ''''
        This:
        Reads and resamples the dataset.
        Writes out this resampled dataset and details about the original dataset
        Reads the resampled_dataset
        Checks we read back in the same array, spacing and origin
        '''
        target_size = 100
        reader = ImageReader(file_name=self.hdf5_filename_3D,
                             target_size=target_size,
                             resample_z=True,
                             hdf5_dataset_name="ImageData")

        file_to_write = 'downsampled_image.hdf5'
        resampled_image = reader.Read()
        resampled_image_array = Converter.vtk2numpy(resampled_image)

        resampled_image_attrs = reader.GetLoadedImageAttrs()
        original_image_attrs = reader.GetOriginalImageAttrs()

        # writer = ImageWriter(file_name=file_to_write, format='hdf5', datasets=[None, resampled_image], attributes=[original_image_attrs, resampled_image_attrs])
        # writer.write()

        writer = cilviewerHDF5Writer()
        writer.SetFileName(file_to_write)
        writer.SetOriginalDataset(None, original_image_attrs)
        writer.AddChildDataset(resampled_image, resampled_image_attrs)
        writer.Write()

        reader = cilviewerHDF5Reader()
        reader.SetFileName(file_to_write)
        reader.Update()
        read_resampled_image = reader.GetOutputDataObject(0)
        read_resampled_image_array = Converter.vtk2numpy(read_resampled_image)

        np.testing.assert_array_equal(resampled_image_array, read_resampled_image_array)
        np.testing.assert_array_equal(resampled_image.GetOrigin(), read_resampled_image.GetOrigin())
        np.testing.assert_array_equal(resampled_image.GetSpacing(), read_resampled_image.GetSpacing())

    def tearDown(self):
        files = [self.hdf5_filename_3D] + self.tiff_fnames
        for f in files:
            os.remove(f)
        os.rmdir('tiff_files')


if __name__ == '__main__':
    unittest.main()
