''''
This example:
1. Writes an example dataset to a file: example_dataset.npy
2. Reads and resamples the dataset.
3. Writes out this resampled dataset and details about the original dataset to resampled_dataset.hdf5
4. prints the structure of this hdf5 file we have written out
5. Reads the resampled_dataset.hdf5
6. Displays the resulting dataset on the viewer.

Note: to test if it works with a real dataset, set DATASET_TO_READ to a filepath containing
a dataset, this will skip step 1 and read in your dataset instead.

'''

from ccpi.viewer.utils.io import ImageReader
from ccpi.viewer.utils.io import ImageWriter, vortexHDF5ImageReader
import h5py
from ccpi.viewer.iviewer import iviewer

DATASET_TO_READ = r"D:\lhe97136\Work\CCPi\CILViewer\Wrappers\Python\ccpi\viewer\cli\24737_fd_normalised.nxs"
TARGET_SIZE = (100)**3
FILE_TO_WRITE = 'resampled_dataset.hdf5'


# --- UTILS ---------------------------------
def descend_obj(obj, sep='\t'):
    """
    Iterate through groups in a HDF5 file and prints the groups and datasets names and datasets attributes
    """
    if type(obj) in [h5py._hl.group.Group, h5py._hl.files.File]:
        for key in obj.keys():
            print(sep, '-', key, ':', obj[key])
            descend_obj(obj[key], sep=sep+'\t')
    elif type(obj) == h5py._hl.dataset.Dataset:
        for key in obj.attrs.keys():
            print(sep+'\t', '-', key, ':', obj.attrs[key])


def h5dump(path, group='/'):
    """
    print HDF5 file metadata

    group: you can give a specific group, defaults to the root group
    """
    with h5py.File(path, 'r') as f:
        descend_obj(f[group])


# ----- STEP 1 ------------------------------

# TODO

# ----- STEP 2 ------------------------------
reader = ImageReader()
reader.set_up(file_name=DATASET_TO_READ, target_size=TARGET_SIZE, resample_z=True)
resampled_image = reader.read()

resampled_image_attrs = reader.get_loaded_image_attrs()
original_image_attrs = reader.get_original_attrs()

# ----- STEP 3 ------------------------------
writer = ImageWriter(file_name=FILE_TO_WRITE, format='hdf5', datasets=[None, resampled_image], attributes=[original_image_attrs, resampled_image_attrs])
writer.write()

# ---- STEP 4 --------------------------------
h5dump(FILE_TO_WRITE)

print(resampled_image)

# ---- STEP 5 --------------------------------
reader = vortexHDF5ImageReader()
reader.SetFileName(FILE_TO_WRITE)
reader.Update()
read_resampled_image = reader.GetOutputDataObject(0)

# ---- STEP 6 --------------------------------
iviewer(read_resampled_image)


