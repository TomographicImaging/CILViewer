import numpy as np
from ccpi.viewer.utils.conversion import calculate_target_downsample_magnification

def calculate_target_downsample_shape(max_size, total_size, shape, acq=False):
    slice_per_chunk, xy_axes_magnification = \
        calculate_target_downsample_magnification(max_size, total_size, acq)
    num_chunks = 1 + len([i for i in range(slice_per_chunk, shape[2], slice_per_chunk)])

    target_image_shape = (int(xy_axes_magnification * shape[0]), int(xy_axes_magnification * shape[1]), num_chunks)
    return target_image_shape