''''
This example:
1. Writes an example dataset to a file: example_dataset.npy
2. Reads and resamples the dataset.
3. Writes out this resampled dataset and details about the original dataset to resampled_dataset.hdf5
4. prints the structure of this hdf5 file we have written out
5. Reads the resampled_dataset.hdf5
6. Writes out the resampled dataset from step 2 to a metaimage file: resampled_dataset_2.mha using the ImageWriter
7. Reads the resampled_dataset_2.mha
8. Displays the resulting datasets on the viewer.

Note: to test if it works with a real dataset, set DATASET_TO_READ to a filepath containing
a dataset, this will skip step 1 and read in your dataset instead.

'''

from ccpi.viewer.utils.io import ImageReader
from ccpi.viewer.utils.io import cilviewerHDF5ImageReader, cilviewerHDF5Writer, ImageWriter
import h5py
from ccpi.viewer.iviewer import iviewer
import numpy as np
import vtk

DATASET_TO_READ = None
TARGET_SIZE = (100)**3
FILE_TO_WRITE = 'resampled_dataset.hdf5'
LOG_FILE = 'image_reader_and_writer.log'
SECOND_FILE_TO_WRITE = 'resampled_dataset_2.mha'


# --- UTILS ---------------------------------
def descend_hdf5_obj(obj, sep='\t'):
    """
    Iterates through the groups in a HDF5 file (obj)
    and prints the groups and datasets names and 
    datasets attributes
    """
    if type(obj) in [h5py._hl.group.Group, h5py._hl.files.File]:
        for key in obj.keys():
            print(sep, '-', key, ':', obj[key])
            descend_hdf5_obj(obj[key], sep=sep + '\t')
    elif type(obj) == h5py._hl.dataset.Dataset:
        for key in obj.attrs.keys():
            print(sep + '\t', '-', key, ':', obj.attrs[key])


def print_hdf5_metadata(path, group='/'):
    """
    print HDF5 file metadata
    path: (str)
        path of hdf5 file
    group: (str), default: '/'
        a specific group to print the metadata for,
        defaults to the root group
    """
    with h5py.File(path, 'r') as f:
        descend_hdf5_obj(f[group])


# ----- STEP 1 ------------------------------

if DATASET_TO_READ is None:
    input_3D_array = np.random.random(size=(500, 100, 600))
    # write to NUMPY: ----------
    DATASET_TO_READ = 'test_3D_data.npy'
    np.save(DATASET_TO_READ, input_3D_array)

# ----- STEP 2 ------------------------------
reader = ImageReader(file_name=DATASET_TO_READ, target_size=TARGET_SIZE, resample_z=True, log_file=LOG_FILE)
resampled_image = reader.Read()

resampled_image_attrs = reader.GetLoadedImageAttrs()
original_image_attrs = reader.GetOriginalImageAttrs()

# ----- STEP 3 ------------------------------
writer = cilviewerHDF5Writer()
writer.SetFileName(FILE_TO_WRITE)
# format='hdf5'
writer.SetOriginalDataset(None, original_image_attrs)
writer.AddChildDataset(resampled_image, resampled_image_attrs)
writer.Write()

# ---- STEP 4 --------------------------------
print_hdf5_metadata(FILE_TO_WRITE)

# ---- STEP 5 --------------------------------
reader = cilviewerHDF5ImageReader()
reader.SetFileName(FILE_TO_WRITE)
reader.Update()
read_resampled_image = reader.GetOutputDataObject(0)

print(read_resampled_image.GetOrigin())
print(read_resampled_image.GetSpacing())

# ---- STEP 6 --------------------------------
writer = ImageWriter()
writer.SetFileName(SECOND_FILE_TO_WRITE)
writer.SetFileFormat('mha')
writer.AddChildDataset(resampled_image)
writer.Write()

# ---- STEP 7 --------------------------------
reader = vtk.vtkMetaImageReader()
reader.SetFileName(SECOND_FILE_TO_WRITE)
reader.Update()
read_resampled_image2 = reader.GetOutputDataObject(0)

print(read_resampled_image2.GetOrigin())
print(read_resampled_image2.GetSpacing())

# ---- STEP 8 --------------------------------
iviewer(read_resampled_image, read_resampled_image2)
