import os
import unittest

import numpy as np
import vtk
from ccpi.viewer.utils.conversion import (Converter, cilRawCroppedReader, cilMetaImageCroppedReader,
                                          cilNumpyCroppedReader, vortexTIFFCroppedReader)


class TestCroppedReaders(unittest.TestCase):

    def setUp(self):
        # Generate random 3D array and write to HDF5:
        np.random.seed(1)
        shape = (5, 4, 6) # was 10 times larger
        bits = 8
        self.input_3D_array = np.random.randint(10, size=shape, dtype=eval(f"np.uint{bits}"))
        self.input_3D_array = np.reshape(np.arange(self.input_3D_array.size),
                                         newshape=shape).astype(dtype=eval(f"np.uint{bits}"))
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
        # Write TIFFs
        fnames = []
        arr = self.input_3D_array
        from PIL import Image
        for i in range(arr.shape[0]):
            fname = 'tiff_test_file_{:03d}.tiff'.format(i)
            fnames.append(os.path.abspath(fname))
            # Using vtk the Y axis gets reversed
            # vtk_image = Converter.numpy2vtkImage(np.expand_dims(arr[i,:,:], axis=0))
            # twriter.SetFileName(fnames[-1])
            # twriter.SetInputData(vtk_image)
            # twriter.Write()
            im = Image.fromarray(arr[i])
            im.save(fnames[-1])

        self.tiff_fnames = fnames

    def check_extent(self, reader, target_z_extent):
        reader.Update()
        image = reader.GetOutput()
        extent = list(image.GetExtent())
        og_shape = np.shape(self.input_3D_array)
        og_extent = [0, og_shape[2] - 1, 0, og_shape[1] - 1, 0, og_shape[0] - 1]
        expected_extent = og_extent
        expected_extent[4] = target_z_extent[0]
        expected_extent[5] = target_z_extent[1]
        self.assertEqual(extent, expected_extent)

    def check_values(self, target_z_extent, read_cropped_image):
        read_cropped_array = Converter.vtk2numpy(read_cropped_image)
        cropped_array = self.input_3D_array[target_z_extent[0]:target_z_extent[1] + 1, :, :]
        np.testing.assert_array_equal(cropped_array, read_cropped_array)
        
    def test_raw_cropped_reader(self):
        target_z_extent = [1, 3]
        reader = cilRawCroppedReader()
        og_shape = np.shape(self.input_3D_array)
        reader.SetFileName(self.raw_filename_3D)
        reader.SetTargetZExtent(tuple(target_z_extent))
        reader.SetBigEndian(False)
        reader.SetIsFortran(False)
        raw_type_code = str(self.input_3D_array.dtype)
        reader.SetTypeCodeName(raw_type_code)
        reader.SetStoredArrayShape(og_shape)
        self.check_extent(reader, target_z_extent)
        self.check_values(target_z_extent, reader.GetOutput())
        # Check raw type code was set correctly:
        self.assertEqual(raw_type_code, reader.GetTypeCodeName())

    def test_meta_and_numpy_cropped_readers(self):
        readers = [cilNumpyCroppedReader(), cilMetaImageCroppedReader()]
        filenames = [self.numpy_filename_3D, self.meta_filename_3D]
        subtest_labels = ['cilNumpyCroppedReader', 'cilMetaImageCroppedReader']
        for i, reader in enumerate(readers):
            with self.subTest(reader=subtest_labels[i]):
                filename = filenames[i]
                target_z_extent = [1, 3]
                reader.SetFileName(filename)
                reader.SetTargetZExtent(tuple(target_z_extent))
                self.check_extent(reader, target_z_extent)
                self.check_values(target_z_extent, reader.GetOutput())

    def test_tiff_cropped_reader(self):
        target_z_extent = [1, 3]
        reader = vortexTIFFCroppedReader()
        # og_shape = np.shape(self.input_3D_array)
        reader.SetFileName(self.tiff_fnames)
        reader.SetTargetZExtent(tuple(target_z_extent))
        raw_type_code = str(self.input_3D_array.dtype)
        self.check_extent(reader, target_z_extent)
        # Check raw type code was set correctly:
        self.assertEqual(raw_type_code, reader.GetTypeCodeName())
        self.check_values(target_z_extent, reader.GetOutput())
        
    def tearDown(self):
        files = [self.raw_filename_3D, self.numpy_filename_3D, self.meta_filename_3D] + self.tiff_fnames
        for f in files:
            os.remove(f)


if __name__ == '__main__':
    unittest.main()
