from argparse import ArgumentParser

import yaml
import schema
from schema import SchemaError, Schema, Optional

from ccpi.viewer.utils.io import ImageReader, ImageWriter

'''
This command line tool takes a dataset file and a yaml file as input.
It resamples or crops the dataset as it reads it in, and then writes
out the resulting dataset to a file.

Supported file types for reading:
hdf5, nxs, mha, raw, numpy

Supported file types for writing:
hdf5, nxs, mha

'''

EXAMPLE_YAML_FILE = '''
EXAMPLE INPUT YAML FILE:

input:
    file_name: '24737_fd_normalised.nxs'
    shape: (1024,1024,1024)
    is_fortran: False
    is_big_endian: True
    typecode: 'float32'
    dataset_name: '/entry1/tomo_entry/data/data' # valid for HDF5 and Zarr
resample:
    target_size: 1
    resample_z: True
output:
    file_name: 'this_fname.nxs'
    format: 'hdf5' # npy, METAImage, NIFTI (or Zarr to come)
'''
'''

THIS IS WHAT THE OUTPUT STRUCTURE OF AN EXAMPLE OUTPUT HDF5 FILE WOULD LOOK LIKE:
Entry 1 contains attributes of the original dataset
Entry 2 contains the resampled dataset and attributes

- entry1 : <HDF5 group "/entry1" (1 members)>
            - tomo_entry : <HDF5 group "/entry1/tomo_entry" (1 members)>
                    - data : <HDF5 group "/entry1/tomo_entry/data" (1 members)>
                            - data : <HDF5 dataset "data": shape (500, 100, 600), type "<f4">
                                            - bit_depth : 64
                                            - file_name : test_3D_data.npy
                                            - header_length : 128
                                            - is_big_endian : False
                                            - origin : [0. 0. 0.]
                                            - shape : [500 100 600]
                                            - spacing : [1 1 1]
                                            - resampled: False
                                            - cropped: False
    - entry2 : <HDF5 group "/entry2" (1 members)>
            - tomo_entry : <HDF5 group "/entry2/tomo_entry" (1 members)>
                    - data : <HDF5 group "/entry2/tomo_entry/data" (1 members)>
                            - data : <HDF5 dataset "data": shape (500, 18, 109), type "<f8">
                                            - cropped : False
                                            - origin : [2.23861279 2.23861279 0.        ]
                                            - resample_z : True
                                            - resampled : True
                                            - spacing : [5.47722558 5.47722558 1.        ]
                                            - original_dataset: /entry1/tomo_entry/data/data
'''
 

# This validates the input yaml file:
schema = Schema(
        {   'input': {'file_name': str,
                        Optional('shape'): tuple, # only for raw
                        Optional('is_fortran'): bool, # only for raw
                        Optional('is_big_endian'): bool, # only for raw
                        Optional('typecode'): str, # only for raw
                        Optional('dataset_name'): str}, # only for hdf5 # need to set default
            'resample': {'target_size': float, 
                         'resample_z' : bool},
            'output': {'file_name': str,
                       'format': str}
        }
    )



def parse_arguments():
    parser = ArgumentParser(prog = 'resampler', 
        description='Resamples a dataset file & writes out to a file.' +
            ' Either specify a yaml file or set at minimum: -i, -o and -target_size')

    parser.add_argument('-f', help='Input yaml file. May be used in place of all other arguments. If set, all other arguments are ignored.', type=str)
    parser.add_argument('--example', help= 'Prints an example input yaml file.', action= 'store_true')

    parser.add_argument('-i', help= 'Input dataset filename. Required if -f is not set.')
    parser.add_argument('--dataset_name', help='Dataset name, only required if input file is HDF5/Nexus format.', type=str, default='/entry1/tomo_entry/data/data')
    parser.add_argument('--shape', help='Shape of input dataset file, only required if input file is raw format.', type=lambda s: [int(item) for item in s.strip('[').strip(']').split(',')])
    parser.add_argument('--is_fortran', help='Whether input dataset file is fortran order, only required if input file is raw format.')
    parser.add_argument('--is_big_endian', help='Whether input dataset file is big endian, only required if input file is raw format.')
    parser.add_argument('--typecode', help='Typecode of input dataset, only required if input file is raw format.', type=str)
    
    
    parser.add_argument('-target_size', help= 'Target size to downsample dataset to, in MB. Required if -f is not set.', type=float)
    parser.add_argument('--resample_z', help= 'Whether to resample along the z axis of the dataset. Optional.', default=True)

    parser.add_argument('-o', help= 'Output filename. Required if -f is not set.')
    parser.add_argument('--out_format', help='File format to write downsampled data to', choices=['hdf5', 'nxs', 'mha'], type=str, default='nxs')

    args = parser.parse_args()

    return args

def get_params_from_args(args):

    if args.f is not None:

        with open(args.f) as f:
            params_raw = yaml.safe_load(f)
            params = {}
            for key, dict in params_raw.items():
                # each of the values in data_raw is a dict
                params[key] = {}
                for sub_key, value in dict.items():
                    try:
                        params[key][sub_key] = eval(value)
                    except:
                        params[key][sub_key] = value
        try:
            schema.validate(params)
        except SchemaError as e:
            print(e)

    else:
        for a in [args.i, args.target_size, args.o]:
            if a is None:
                raise Exception("If yaml file is not set: -i, --target_size, and -o must be set")

        params = {'input': {'file_name': args.i},
                  'resample': {'target_size': args.target_size},
                  'output': {'file_name': args.o}}

        args_input = ['shape',  'typecode', 'dataset_name']
        bool_args_input = ['is_fortran', 'is_big_endian']

        for a in args_input:
            if eval(f"args.{a}") is not None:
                params['input'][a] = eval(f"args.{a}")
        
        for a in bool_args_input:
            if eval(f"args.{a}") is not None:
                params['input'][a] = eval(eval(f"args.{a}"))

        if args.resample_z is not None:
            params['resample']['resample_z'] = eval(args.resample_z)

        if args.out_format is not None:
            params['output']['format'] = args.out_format

    return params
        


def main():
    args = parse_arguments()
    # Do nothing else if we are just printing an example yaml file:
    if args.example:
        print(EXAMPLE_YAML_FILE)
        return
    params = get_params_from_args(args)

    raw_attrs = None
    dataset_name = None
    if 'input' in params.keys():
        raw_attrs = {}
        for key, value in params['input'].items():
            if key == 'dataset_name':
                dataset_name = value
            elif key == 'file_name':
                pass
            else:
                raw_attrs[key] = value

    target_size = params['resample']['target_size']
    if target_size is not None:
        target_size *= 1e6

    reader = ImageReader(file_name=params['input']['file_name'], resample=True, target_size=target_size,
            resample_z=params['resample']['resample_z'], raw_image_attrs=raw_attrs, hdf5_dataset_name=dataset_name)
    downsampled_image = reader.Read()
    original_image_attrs = reader.GetOriginalImageAttrs()
    loaded_image_attrs = reader.GetLoadedImageAttrs()
    
    writer = ImageWriter()
    writer.SetFileName(params['output']['file_name'])
    writer.SetFileFormat(params['output']['format'])
    writer.SetOriginalDataset(None, original_image_attrs)
    writer.AddChildDataset(downsampled_image,  loaded_image_attrs)
    writer.Write()

if __name__ == '__main__':
    main()
