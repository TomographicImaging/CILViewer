import os
import unittest

import numpy as np
import vtk
from ccpi.viewer.utils.conversion import (Converter, cilRawResampleReader, cilMetaImageResampleReader,
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

    def test_WriteMETAImageHeader(self):
        '''writes a mhd file to go with a raw 
        datafile, using cilNumpyMETAImageWriter.WriteMETAImageHeader and then tests if this can
        be read successfully with vtk.vtkMetaImageReader
        by comparing to array read with cilRawResampleReader
        directly from RawResampleReader and the original contents'''

        # read raw file's info:
        data_filename = self.raw_filename_3D
        header_filename = 'raw_header.mhd'
        typecode = 'uint8'
        big_endian = False
        header_length = 0
        shape = np.shape(self.input_3D_array)
        shape_to_write = shape[::-1]  # because it is not a fortran order array we have to swap
        cilNumpyMETAImageWriter.WriteMETAImageHeader(data_filename,
                                                     header_filename,
                                                     typecode,
                                                     big_endian,
                                                     header_length,
                                                     shape_to_write,
                                                     spacing=(1., 1., 1.),
                                                     origin=(0., 0., 0.))

        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(header_filename)
        reader.Update()
        read_mhd_raw = Converter.vtk2numpy(reader.GetOutput())

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

        np.testing.assert_array_equal(read_mhd_raw, raw_array)
        np.testing.assert_array_equal(read_mhd_raw, self.input_3D_array)

    def tearDown(self):
        files = [self.raw_filename_3D]
        for f in files:
            os.remove(f)


if __name__ == '__main__':
    unittest.main()
