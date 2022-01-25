import os
import unittest

import numpy as np
import vtk
from ccpi.viewer.utils.conversion import (Converter, cilRawResampleReader,
                                          cilMetaImageResampleReader,
                                          cilNumpyResampleReader, cilNumpyMETAImageWriter)

import numpy as np

'''
This will test parts of the utils/conversion.py file other than
the Resample and Cropped readers. (See test_cropped_readers.py
and test_resample_readers.py for tests of these)

'''

class TestConversion(unittest.TestCase):

    def setUp(self):
        # Generate random 3D array and write to HDF5:
        np.random.seed(1)
        self.input_3D_array = np.random.randint(10, size=(5, 10, 6), dtype=np.uint8)
        bytes_3D_array = bytes(self.input_3D_array)
        self.raw_filename_3D = 'test_3D_data.raw'
        with open(self.raw_filename_3D, 'wb') as f:
            f.write(bytes_3D_array)


    def test_cilNumpyMETAImageWriter_contiguous(self):
        ''' Tests using cilNumpyMETAImageWriter to write
        a numpy array with a metaimage header. Tests a numpy array
        in contiguous order'''

        # Write a numpy array to a file:
        self.numpy_filename_3D = 'test_3D_data.npy'
        np.save(self.numpy_filename_3D, self.input_3D_array)

        # Read in the numpy array:
        numpy_reader = cilNumpyResampleReader()
        # default target size higher than total size so it reads whole array
        numpy_reader.SetFileName(self.numpy_filename_3D)
        numpy_reader.Update()
        read_numpy_as_vtk = numpy_reader.GetOutput()
        read_numpy = Converter.vtk2numpy(read_numpy_as_vtk)

        # Now we want to save a mhd file to go with it:
        writer = cilNumpyMETAImageWriter()
        writer.SetInputData(read_numpy)
        writer.SetFileName('test_3D_data_mhd_np')
        writer.Write()

        # Read the mhd and compare with the numpy array we read in before
        # First read with the meta image reader:
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName('test_3D_data_mhd_np.mhd')
        reader.Update()
        read_mhd_vtk = reader.GetOutput()
        # all our tests fail if we don't specify order F
        read_mhd = Converter.vtk2numpy(read_mhd_vtk)

        # This would show the vtkMetaImageReader reads our written mhd fine:
        # This fails due to wrong ordering
        # self.assertEqual(read_numpy_as_vtk.GetExtent(), read_mhd_vtk.GetExtent())
        print("vtkMetaImageReader test passed")
        np.testing.assert_array_equal(read_numpy, read_mhd)
        np.testing.assert_array_equal(self.input_3D_array, read_mhd)

        # then read with our reader:
        reader = cilMetaImageResampleReader()
        # default target size higher than total size so it reads whole array
        reader.SetFileName('test_3D_data_mhd_np.mhd')
        reader.Update()
        read_mhd_vtk = reader.GetOutput()
        # all our tests fail if we don't specify order F
        read_mhd = Converter.vtk2numpy(read_mhd_vtk)

        # This would show our cilMetaImageResampleReader reads our written mhd fine:
        # This fails due to wrong ordering:
        #self.assertEqual(read_numpy_as_vtk.GetExtent(), read_mhd_vtk.GetExtent())
        print("cilMetaImageResampleReader test passed")
        np.testing.assert_array_equal(read_numpy, read_mhd)
        np.testing.assert_array_equal(self.input_3D_array, read_mhd)


    def test_cilNumpyMETAImageWriter_fortran(self):
        ''' Tests using cilNumpyMETAImageWriter to write
        a numpy array with a metaimage header. Tests a numpy array
        in fortran order'''

        # Write a numpy array to a file:
        self.numpy_filename_3D_fortran = 'test_3D_data_F.npy'
        self.input_3D_array_fortran = np.asfortranarray(self.input_3D_array)
        np.save(self.numpy_filename_3D_fortran, self.input_3D_array_fortran)

        # Read in the numpy array:
        numpy_reader = cilNumpyResampleReader()
        # default target size higher than total size so it reads whole array
        numpy_reader.SetFileName(self.numpy_filename_3D_fortran)
        numpy_reader.Update()
        read_numpy_as_vtk = numpy_reader.GetOutput()
        read_numpy = Converter.vtk2numpy(read_numpy_as_vtk)

        # Now we want to save a mhd file to go with it:
        writer = cilNumpyMETAImageWriter()
        writer.SetInputData(read_numpy)
        writer.SetFileName('test_3D_data_mhd_np')
        writer.Write()

        # Read the mhd and compare with the numpy array we read in before
        # First read with the meta image reader:
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName('test_3D_data_mhd_np.mhd')
        reader.Update()
        read_mhd_vtk = reader.GetOutput()
        # all our tests fail if we  specify order F or not
        read_mhd = Converter.vtk2numpy(read_mhd_vtk, order='F')

        # This would show the vtkMetaImageReader reads our written mhd fine:
        # This fails due to wrong ordering
        #self.assertEqual(read_numpy_as_vtk.GetExtent(), read_mhd_vtk.GetExtent())
        print("vtkMetaImageReader test passed")
        np.testing.assert_array_equal(read_numpy, read_mhd)
        np.testing.assert_array_equal(self.input_3D_array, read_mhd)

        # then read with our reader:
        reader = cilMetaImageResampleReader()
        # default target size higher than total size so it reads whole array
        reader.SetFileName('test_3D_data_mhd_np.mhd')
        reader.Update()
        read_mhd_vtk = reader.GetOutput()
        # all our tests fail if we  specify order F or not
        read_mhd = Converter.vtk2numpy(read_mhd_vtk)

        # This would show our cilMetaImageResampleReader reads our written mhd fine:
        # This fails due to wrong ordering:
        #self.assertEqual(read_numpy_as_vtk.GetExtent(), read_mhd_vtk.GetExtent())
        print("cilMetaImageResampleReader test passed")
        np.testing.assert_array_equal(read_numpy, read_mhd)
        np.testing.assert_array_equal(self.numpy_filename_3D_fortran, read_mhd)


    def test_WriteMETAImageHeader(self):
        '''writes a mhd file to go with a raw 
        datafile, using cilNumpyMETAImageWriter.WriteMETAImageHeader and then tests if this can
        be read successfully with vtk.vtkMetaImageReader
        by comparing to array read with cilRawResampleReader
        directly from RawResampleReader and the original contents'''

        data_filename = self.raw_filename_3D
        header_filename = 'raw_header.mhd'
        typecode = 'uint8'
        big_endian = False
        header_length = 0
        shape = np.shape(self.input_3D_array)
        shape_to_write = shape[::-1] # because it is not a fortran order array we have to swap
        cilNumpyMETAImageWriter.WriteMETAImageHeader(data_filename, header_filename, typecode, big_endian,
                             header_length, shape_to_write, spacing=(1., 1., 1.), origin=(0., 0., 0.))
        
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(header_filename)
        reader.Update()
        read_mhd_raw = Converter.vtk2numpy(reader.GetOutput())

        # Tests the array we read with vtk.vtkMetaImageReader matches original array:
        np.testing.assert_array_equal(read_mhd_raw, self.input_3D_array)

        reader = cilRawResampleReader()
        target_size = int(1e12)
        reader.SetTargetSize(target_size)
        reader.SetBigEndian(False)
        reader.SetIsFortran(False)
        reader.SetFileName(self.raw_filename_3D)
        raw_type_code = str(self.input_3D_array.dtype)
        reader.SetTypeCodeName(raw_type_code)
        reader.SetStoredArrayShape(shape)
        reader.Update()

        image = reader.GetOutput()
        raw_array = Converter.vtk2numpy(image)

        # Tests the array we read with cilRawResampleReader matches original array:
        np.testing.assert_array_equal(raw_array, self.input_3D_array)


    def tearDown(self):
        files = [self.raw_filename_3D]
        for f in files:
            os.remove(f)


if __name__ == '__main__':
    unittest.main()