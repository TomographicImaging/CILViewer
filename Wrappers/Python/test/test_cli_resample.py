import os
import unittest

import numpy as np
import os
import unittest

import h5py
import numpy as np
import vtk
from ccpi.viewer.utils.conversion import Converter
from ccpi.viewer.utils.io import cilviewerHDF5Reader
import yaml

from os import system


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


class TestCLIResample(unittest.TestCase):

    def setUp(self):
        # Generate random 3D array:
        bits = 16
        self.bytes_per_element = int(bits / 8)
        self.input_3D_array = np.random.randint(10, size=(5, 10, 6), dtype=eval(f"np.uint{bits}"))

        # write to HDF5: -----------
        self.hdf5_filename_3D = 'test_3D_data.h5'
        self.hdf5_yaml_filename = 'test_hdf5.yaml'
        with h5py.File(self.hdf5_filename_3D, 'w') as f:
            f.create_dataset('/entry1/tomo_entry/data/data', data=self.input_3D_array)

        self.hdf5_dict = {
            'input': {
                'file_name': self.hdf5_filename_3D,
                'dataset_name': '/entry1/tomo_entry/data/data'
            },
            'resample': {
                'target_size': 100e-6,
                'resample_z': False
            },
            'output': {
                'file_name': 'test_hdf5_out.hdf5',
                'format': 'hdf5'
            }
        }
        with open(self.hdf5_yaml_filename, 'w') as file:
            yaml.dump(self.hdf5_dict, file)

        # write to raw: -------------
        bytes_3D_array = bytes(self.input_3D_array)
        self.raw_filename_3D = 'test_3D_data.raw'
        self.raw_yaml_filename = 'test_raw.yaml'
        with open(self.raw_filename_3D, 'wb') as f:
            f.write(bytes_3D_array)
        self.raw_dict = {
            'input': {
                'file_name': self.raw_filename_3D,
                'shape': str(np.shape(self.input_3D_array)),
                'is_fortran': False,
                'is_big_endian': False,
                'typecode': str(self.input_3D_array.dtype)
            },
            'resample': {
                'target_size': 100e-6,
                'resample_z': False
            },
            'output': {
                'file_name': 'test_raw_out.hdf5',
                'format': 'hdf5'
            }
        }
        with open(self.raw_yaml_filename, 'w') as file:
            yaml.dump(self.raw_dict, file)

    def _test_resampling_acq_data(self, reader, target_size):
        og_shape = np.shape(self.input_3D_array)
        og_shape = (og_shape[2], og_shape[1], og_shape[0])
        og_size = og_shape[0] * og_shape[1] * og_shape[2] * self.bytes_per_element
        reader.Update()
        image = reader.GetOutputDataObject(0)
        extent = image.GetExtent()

        shape = calculate_target_downsample_shape(target_size, og_size, og_shape, acq=True)
        expected_size = shape[0] * shape[1] * shape[2]
        resulting_shape = (extent[1] + 1, (extent[3] + 1), (extent[5] + 1))
        resulting_size = resulting_shape[0] * \
            resulting_shape[1]*resulting_shape[2]
        # angle (z direction) is first index in numpy array, and in cil
        # but it is the last in vtk.
        resulting_z_shape = extent[5] + 1
        og_z_shape = np.shape(self.input_3D_array)[0]

        self.assertEqual(resulting_size, expected_size)
        self.assertEqual(resulting_z_shape, og_z_shape)

    def test_resample_with_yaml(self):
        dicts = [self.hdf5_dict, self.raw_dict]
        filenames = [self.hdf5_yaml_filename, self.raw_yaml_filename]
        subtest_labels = ['HDF5', 'raw']
        for i, dict in enumerate(dicts):
            with self.subTest(format=subtest_labels[i]):
                yaml_file = filenames[i]

            # Tests image with correct target size is generated by resample reader:
            system('resample -f {}'.format(yaml_file))

            reader = cilviewerHDF5Reader()
            reader.SetFileName(dict['output']['file_name'])
            target_size = int(dict['resample']['target_size'] * 1e6)
            self._test_resampling_acq_data(reader, target_size)

    def test_resample_command_line_hdf5(self):
        dict = self.hdf5_dict

        # Tests image with correct target size is generated by resample reader:
        input_file = dict['input']['file_name']
        target_size = dict['resample']['target_size']
        resample_z = dict['resample']['resample_z']
        out = dict['output']['file_name']
        out_format = dict['output']['format']

        # specific to hdf5:
        dset_name = dict['input']['dataset_name']

        command = f'resample -i {input_file} --dataset_name {dset_name} -o {out} -target_size {target_size} --resample_z {resample_z} --out_format {out_format}'

        if system(command) != 0:
            raise Exception("Error running test_resample_command_line_hdf5")

        reader = cilviewerHDF5Reader()
        reader.SetFileName(dict['output']['file_name'])

        target_size = int(target_size * 1e6)
        self._test_resampling_acq_data(reader, target_size)

    def test_resample_command_line_raw(self):
        dict = self.raw_dict

        # Tests image with correct target size is generated by resample reader:
        input_file = dict['input']['file_name']
        target_size = dict['resample']['target_size']
        resample_z = dict['resample']['resample_z']
        out = dict['output']['file_name']
        out_format = dict['output']['format']

        # specific to raw:
        shape = list(eval(dict['input']['shape']))
        shape = f"{shape[0]},{shape[1]},{shape[2]}"
        # is_fortran = dict['input']['is_fortran']
        is_fortran = False
        is_big_endian = dict['input']['is_big_endian']
        typecode = dict['input']['typecode']

        command = f'resample -i {input_file} --shape {shape} --is_fortran {is_fortran} --is_big_endian {is_big_endian} --typecode {typecode} -o {out} -target_size {target_size} --resample_z {resample_z} --out_format {out_format}'

        if system(command) != 0:
            raise Exception("Error running test_resample_command_line_raw")

        reader = cilviewerHDF5Reader()
        reader.SetFileName(dict['output']['file_name'])

        target_size = int(target_size * 1e6)
        self._test_resampling_acq_data(reader, target_size)

    def tearDown(self):
        files = [self.hdf5_filename_3D, self.hdf5_yaml_filename, self.raw_filename_3D, self.raw_yaml_filename]
        for f in files:
            os.remove(f)


if __name__ == '__main__':
    unittest.main()
