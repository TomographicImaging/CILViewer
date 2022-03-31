from argparse import ArgumentParser

import yaml
import schema
from schema import SchemaError, Schema, Optional

from ccpi.viewer.utils.io import ImageReader

# SO FAR THIS READS AND DOWNSAMPLES BUT DOESN'T WRITE


schema = Schema(
        {
            Optional('array'): {Optional('shape'): tuple, # only for raw
                                Optional('is_fortran'): bool, # only for raw
                                Optional('is_big_endian'): bool, # only for raw
                                Optional('typecode'): str, # only for raw
                                Optional('group_name'): str}, # only for hdf5 # set default
            'resample': {'target_size': int, 
                         'resample_z' : bool},
            'output': {'filename': str,
                       'format': str}
        }
    )



def main():
    parser = ArgumentParser(description='Dataset to Resample')
    parser.add_argument('input_dataset', help='Input dataset')
    parser.add_argument('yaml_file', help='Input yaml file')

    args = parser.parse_args()

    with open(args.yaml_file) as f:
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

   
    if 'array' in params.keys():
        raw_attrs = {}
        for key, value in params['array'].items():
            if key == 'group_name':
                group_name = value
            else:
                raw_attrs[key] = value
    else:
        raw_attrs = None
        group_name = None


    reader = ImageReader(file_name=args.input_dataset, resample=True, target_size=params['resample']['target_size'],
             resample_z=params['resample']['resample_z'], raw_image_attrs=raw_attrs, hdf5_dataset_name=group_name)
    downsampled_image = reader.read()

    # now we need to write out



if __name__ == '__main__':
    main()
