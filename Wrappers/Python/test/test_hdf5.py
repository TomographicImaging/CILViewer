import os
import unittest

import h5py
import numpy as np
import vtk
from ccpi.viewer.utils.conversion import Converter, cilHDF5ResampleReader, cilHDF5CroppedReader
from ccpi.viewer.utils.hdf5_io import (HDF5Reader, HDF5SubsetReader, write_image_data_to_hdf5)


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


class TestHDF5IO(unittest.TestCase):

    def setUp(self):
        # Generate random 3D array and write to HDF5:
        np.random.seed(1)
        self.input_3D_array = np.random.random(size=(5, 10, 6))
        self.hdf5_filename_3D = 'test_3D_data.h5'
        with h5py.File(self.hdf5_filename_3D, 'w') as f:
            f.create_dataset('ImageData', data=self.input_3D_array)

        # Generate random 4D array and write to HDF5:
        self.input_4D_array = np.random.random(size=(10, 7, 10, 6))
        self.hdf5_filename_4D = 'test_4D_data.h5'
        with h5py.File(self.hdf5_filename_4D, 'w') as f:
            f.create_dataset('ImageData', data=self.input_4D_array)

    def test_read_hdf5(self):
        # Write a numpy array to a HDF5 and then test using
        # HDF5Reader to read it back:
        reader = HDF5Reader()
        reader.SetFileName(self.hdf5_filename_3D)
        reader.SetDatasetName("ImageData")
        reader.Update()
        array_image_data = reader.GetOutputDataObject(0)
        read_array = Converter.vtk2numpy(array_image_data)
        np.testing.assert_array_equal(self.input_3D_array, read_array)

    def test_read_hdf5_channel(self):
        # Test reading a specific channel in a 4D dataset
        channel_index = 5
        reader = HDF5Reader()
        reader.SetFileName(self.hdf5_filename_4D)
        reader.SetDatasetName("ImageData")
        reader.Set4DSliceIndex(channel_index)
        reader.Set4DIndex(0)
        reader.Update()
        array_image_data = reader.GetOutputDataObject(0)
        read_array = Converter.vtk2numpy(array_image_data)
        np.testing.assert_array_equal(self.input_4D_array[channel_index], read_array)

    def test_hdf5_subset_reader(self):
        # With the subset reader: -----------------------------
        # Test cropping the extent of a dataset
        cropped_array = self.input_3D_array[1:3, 3:6, 0:3]
        reader = HDF5Reader()
        reader.SetFileName(self.hdf5_filename_3D)
        reader.SetDatasetName("ImageData")
        cropped_reader = HDF5SubsetReader()
        cropped_reader.SetInputConnection(reader.GetOutputPort())
        # NOTE: the extent is in vtk so is in fortran order, whereas
        # above we had the np array in C-order so x and y cropping swapped
        cropped_reader.SetUpdateExtent((0, 2, 3, 5, 1, 2))
        cropped_reader.Update()
        array_image_data = cropped_reader.GetOutputDataObject(0)
        read_cropped_array = Converter.vtk2numpy(array_image_data)
        np.testing.assert_array_equal(cropped_array, read_cropped_array)

    def test_read_cropped_hdf5_reader(self):
        # # With the Cropped reader: -----------------------------
        cropped_array = self.input_3D_array[1:3, 3:6, 0:3]
        reader = cilHDF5CroppedReader()
        reader.SetFileName(self.hdf5_filename_3D)
        reader.SetDatasetName("ImageData")
        reader.SetTargetExtent((0, 2, 3, 5, 1, 2))
        reader.Update()
        array_image_data = reader.GetOutput()
        read_cropped_array = Converter.vtk2numpy(array_image_data)
        np.testing.assert_array_equal(cropped_array, read_cropped_array)

    def test_read_cropped_hdf5_channel(self):
        # Test cropping the extent of a dataset
        channel_index = 5
        cropped_array = self.input_4D_array[1:2, channel_index, 3:6, 0:3]
        hdf5_filename = 'test_numpy_data.h5'
        with h5py.File(hdf5_filename, 'w') as f:
            f.create_dataset('ImageData', data=self.input_4D_array)
        reader = HDF5Reader()
        reader.SetFileName(self.hdf5_filename_4D)
        reader.SetDatasetName("ImageData")
        reader.Set4DSliceIndex(channel_index)
        reader.Set4DIndex(1)
        cropped_reader = HDF5SubsetReader()
        cropped_reader.SetInputConnection(reader.GetOutputPort())
        # NOTE: the extent is in vtk so is in fortran order, whereas
        # above we had the np array in C-order so x and y cropping swapped
        cropped_reader.SetUpdateExtent((0, 2, 3, 5, 1, 1))
        cropped_reader.Update()
        array_image_data = cropped_reader.GetOutputDataObject(0)
        read_cropped_array = Converter.vtk2numpy(array_image_data)
        np.testing.assert_array_equal(cropped_array, read_cropped_array)

    def test_write_hdf5(self):
        # Provides an example image with extent (-10, 10, -10, 10, -10, 10):
        image_source = vtk.vtkRTAnalyticSource()
        image_source.Update()
        image_data = image_source.GetOutput()
        numpy_data = Converter.vtk2numpy(image_data)

        self.hdf5_filename_RT = "test_image_data.hdf5"

        write_image_data_to_hdf5(self.hdf5_filename_RT, image_data, dataset_name='RTData')

        # Test reading hdf5:
        reader = HDF5Reader()
        reader.SetFileName(self.hdf5_filename_RT)
        reader.SetDatasetName('RTData')
        reader.Update()

        read_image_data = reader.GetOutputDataObject(0)
        read_numpy_data = Converter.vtk2numpy(read_image_data)
        np.testing.assert_array_equal(numpy_data, read_numpy_data)
        # currently fails because we don't save extent to hdf5:
        # self.assertEqual(image_data.GetExtent(), read_image_data.GetExtent())
        os.remove(self.hdf5_filename_RT)

    def test_hdf5_resample_reader(self):
        # Tests image with correct target size is generated by resample reader:
        # Not a great test, but at least checks the resample reader runs
        # without crashing
        # TODO: improve this test
        readerhdf5 = cilHDF5ResampleReader()
        readerhdf5.SetFileName(self.hdf5_filename_3D)
        readerhdf5.SetDatasetName("ImageData")
        target_size = 100
        readerhdf5.SetTargetSize(target_size)
        readerhdf5.Update()
        image = readerhdf5.GetOutput()
        extent = image.GetExtent()
        resulting_shape = (extent[1] + 1, (extent[3] + 1), (extent[5] + 1))
        og_shape = np.shape(self.input_3D_array)
        og_shape = (og_shape[2], og_shape[1], og_shape[0])
        og_size = og_shape[0] * og_shape[1] * og_shape[2] * readerhdf5.GetBytesPerElement()
        expected_shape = calculate_target_downsample_shape(target_size, og_size, og_shape)
        self.assertEqual(resulting_shape, expected_shape)

        # Now test if we get the full image extent if our
        # target size is larger than the size of the image:
        target_size = og_size * 2
        readerhdf5.SetTargetSize(target_size)
        readerhdf5.Update()
        image = readerhdf5.GetOutput()
        extent = image.GetExtent()
        expected_shape = og_shape
        resulting_shape = (extent[1] + 1, (extent[3] + 1), (extent[5] + 1))
        self.assertEqual(resulting_shape, expected_shape)
        resulting_array = Converter.vtk2numpy(image)
        np.testing.assert_array_equal(self.input_3D_array, resulting_array)

        # Now test if we get the correct z extent if we set that we
        # have acquisition data
        readerhdf5 = cilHDF5ResampleReader()
        readerhdf5.SetDatasetName("ImageData")
        readerhdf5.SetFileName(self.hdf5_filename_3D)
        target_size = 100
        readerhdf5.SetTargetSize(target_size)
        readerhdf5.SetIsAcquisitionData(True)
        readerhdf5.Update()
        image = readerhdf5.GetOutput()
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

    def tearDown(self):
        files = [self.hdf5_filename_3D, self.hdf5_filename_4D]
        for f in files:
            os.remove(f)


if __name__ == '__main__':
    unittest.main()
