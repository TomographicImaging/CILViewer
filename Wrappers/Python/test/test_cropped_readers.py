import os
import unittest

import numpy as np
import vtk
from ccpi.viewer.utils.conversion import (Converter, cilRawCroppedReader,
                                          cilMetaImageCroppedReader,
                                          cilNumpyCroppedReader)



class TestCroppedReaders(unittest.TestCase):

    def setUp(self):
        # Generate random 3D array and write to HDF5:
        self.input_3D_array = np.random.randint(10, size=(5, 10, 6), dtype=np.uint8)
        bytes_3D_array = bytes(self.input_3D_array)
        self.raw_filename_3D = 'test_3D_data.raw'
        with open(self.raw_filename_3D, 'wb') as f:
            f.write(bytes_3D_array)

        self.numpy_filename_3D = 'test_3D_data.npy'
        np.save(self.numpy_filename_3D, self.input_3D_array)

        self.meta_filename_3D = 'test_3D_data.mha'
        vtk_image = Converter.numpy2vtkImage(self.input_3D_array)
        writer = vtk.vtkMetaImageWriter()
        writer.SetFileName(self.meta_filename_3D)
        writer.SetInputData(vtk_image)
        writer.SetCompression(False)
        writer.Write()

    def check_extent(self, reader, target_z_extent):
        reader.Update()
        image = reader.GetOutput()
        extent = list(image.GetExtent())
        og_shape = np.shape(self.input_3D_array)
        og_extent = [0, og_shape[2]-1, 0, og_shape[1]-1, 0, og_shape[0]-1]
        expected_extent = og_extent
        expected_extent[4] = target_z_extent[0]
        expected_extent[5] = target_z_extent[1]
        self.assertEqual(extent, expected_extent)

    def test_raw_cropped_reader(self):
        target_z_extent = [1, 3]
        reader = cilRawCroppedReader()
        og_shape = np.shape(self.input_3D_array)
        reader.SetFileName(self.raw_filename_3D)
        reader.SetTargetZExtent(tuple(target_z_extent))
        reader.SetBigEndian(False)
        reader.SetIsFortran(False)
        reader.SetRawTypeCode(str(self.input_3D_array.dtype))
        reader.SetStoredArrayShape(og_shape)
        self.check_extent(reader, target_z_extent)


    def test_meta_and_numpy_cropped_readers(self):
        readers = [cilNumpyCroppedReader(), cilMetaImageCroppedReader()]
        filenames = [self.numpy_filename_3D, self.meta_filename_3D]
        subtest_labels = ['cilNumpyCroppedReader',
                          'cilMetaImageCroppedReader']
        for i, reader in enumerate(readers):
            with self.subTest(reader=subtest_labels[i]):
                filename = filenames[i]
                target_z_extent = [1, 3]
                og_shape = np.shape(self.input_3D_array)
                reader.SetFileName(filename)
                reader.SetTargetZExtent(tuple(target_z_extent))
                self.check_extent(reader, target_z_extent)

    def tearDown(self):
        files = [self.raw_filename_3D]
        for f in files:
            os.remove(f)


if __name__ == '__main__':
    unittest.main()
