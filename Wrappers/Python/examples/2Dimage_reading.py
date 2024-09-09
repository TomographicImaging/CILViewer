from ccpi.viewer.utils.io import ImageReader
from ccpi.viewer.iviewer import iviewer
from ccpi.viewer.CILViewer2D import CILViewer2D
import numpy as np
import vtk
# ----- STEP 1 ------------------------------
DATASET_TO_READ = None
TARGET_SIZE = (100)**3
LOG_FILE = 'image_reader_and_writer.log'
# DATASET_TO_READ = r'C:\Users\zvm34551\Coding_environment\DATA\DVC_dataset\TIFF\TIFF\Frame 0\frame_00_f_crop_idx_0000 - Copy.tiff'
#DATASET_TO_READ = r'C:\Users\zvm34551\Coding_environment\DATA\DVC_dataset\TIFF\TIFF\Frame 0\frame_00_f_crop_idx_0000 - Copy.tiff'
DATASET_TO_READ = r'C:\Users\zvm34551\Coding_environment\DATA\DVC_dataset\TIFF\TIFF\Frame 0\frame_00_f_crop_idx_0600.tiff'
# if DATASET_TO_READ is None:
#     input_3D_array = np.random.random(size=(500, 100, 600))
#     # write to NUMPY: ----------
#     DATASET_TO_READ = 'test_3D_data.npy'
#     np.save(DATASET_TO_READ, input_3D_array)

# ----- STEP 2 ------------------------------
# reader = ImageReader(file_name=DATASET_TO_READ, target_size=TARGET_SIZE, resample_z=True, log_file=LOG_FILE)
# resampled_image = reader.Read()

# resampled_image_attrs = reader.GetLoadedImageAttrs()
# original_image_attrs = reader.GetOriginalImageAttrs()

# ---- STEP 7 --------------------------------
#reader = vtk.vtkMetaImageReader()
reader = vtk.vtkTIFFReader()
reader.SetFileName(DATASET_TO_READ)
reader.Update()
#read_resampled_image2 = reader.GetOutputDataObject(0)

#print(read_resampled_image2.GetOrigin())
#print(read_resampled_image2.GetSpacing())

# ---- STEP 8 --------------------------------

# Try iviewer
#iviewer(read_resampled_image2, read_resampled_image2)

# Try CILViewer2D
v = CILViewer2D()
print(reader.GetOutput())
v.setInputData(reader.GetOutput())
v.startRenderLoop()

# Try ImageReader
ImageReader