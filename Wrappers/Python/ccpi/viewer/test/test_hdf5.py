from ccpi.viewer.utils.hdf5_io import HDF5Reader, write_image_data_to_hdf5, HDF5SubsetReader
import vtk
import unittest
import h5py
import numpy as np
from ccpi.viewer.utils.conversion import Converter
import os


class TestHDF5IO(unittest.TestCase):

    def setUp(self):
        # Generate random 3D array and write to HDF5:
        self.input_3D_array = np.random.random(size=(5, 10, 6))
        self.hdf5_filename_3D = 'test_3D_data.h5'
        with h5py.File(self.hdf5_filename_3D, 'w') as f:
            f.create_dataset('ImageData', data=self.input_3D_array)

        # Generate random 4D array and write to HDF5:
        self.input_4D_array = np.random.random(size=(10, 5, 10, 6))
        self.hdf5_filename_4D = 'test_4D_data.h5'
        with h5py.File(self.hdf5_filename_4D, 'w') as f:
            f.create_dataset('ImageData', data=self.input_4D_array)

    def test_read_hdf5(self):
        # Write a numpy array to a HDF5 and then test using
        # HDF5Reader to read it back:
        reader = HDF5Reader()
        reader.SetFileName(self.hdf5_filename_3D)
        reader.Update()
        array_image_data = reader.GetOutputDataObject(0)
        read_array = Converter.vtk2numpy(array_image_data)
        np.testing.assert_array_equal(self.input_3D_array, read_array)

    def test_read_hdf5_channel(self):
        # Test reading a specific channel in a 4D dataset
        channel_index = 5
        reader = HDF5Reader()
        reader.SetFileName(self.hdf5_filename_4D)
        reader.Set4DIndex(channel_index)
        reader.Update()
        array_image_data = reader.GetOutputDataObject(0)
        read_array = Converter.vtk2numpy(array_image_data)
        np.testing.assert_array_equal(
            self.input_4D_array[channel_index], read_array)

    def test_read_cropped_hdf5(self):
        # Test cropping the extent of a dataset
        cropped_array = self.input_3D_array[1:3, 3:6, 0:3]
        reader = HDF5Reader()
        reader.SetFileName(self.hdf5_filename_3D)
        cropped_reader = HDF5SubsetReader()
        cropped_reader.SetInputConnection(reader.GetOutputPort())
        # NOTE: the extent is in vtk so is in fortran order, whereas
        # above we had the np array in C-order so x and y cropping swapped
        cropped_reader.SetUpdateExtent((0, 2, 3, 5, 1, 2))
        cropped_reader.Update()
        array_image_data = cropped_reader.GetOutputDataObject(0)
        read_cropped_array = Converter.vtk2numpy(array_image_data)
        np.testing.assert_array_equal(cropped_array, read_cropped_array)

    def test_read_cropped_hdf5_channel(self):
        # Test cropping the extent of a dataset
        channel_index = 5
        cropped_array = self.input_4D_array[:, 1:2, 3:6, 0:3][5]
        hdf5_filename = 'test_numpy_data.h5'
        with h5py.File(hdf5_filename, 'w') as f:
            f.create_dataset('ImageData', data=self.input_4D_array)
        reader = HDF5Reader()
        reader.SetFileName(self.hdf5_filename_4D)
        reader.Set4DIndex(channel_index)
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

        write_image_data_to_hdf5(
            self.hdf5_filename_RT, image_data, label='RTData',
            array_name='RTData')

        # Test reading hdf5:
        reader = HDF5Reader()
        reader.SetFileName(self.hdf5_filename_RT)
        reader.SetLabel('RTData')
        reader.Update()

        read_image_data = reader.GetOutputDataObject(0)
        read_numpy_data = Converter.vtk2numpy(read_image_data)
        np.testing.assert_array_equal(numpy_data, read_numpy_data)
        # self.assertEqual(image_data.GetExtent(), read_image_data.GetExtent()) # currently fails
        os.remove(self.hdf5_filename_RT)

    def tearDown(self):
        files = [self.hdf5_filename_3D,
                 self.hdf5_filename_4D]
        for f in files:
            os.remove(f)


if __name__ == '__main__':
    unittest.main()
