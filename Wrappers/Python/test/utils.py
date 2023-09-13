import numpy as np

def calculate_target_downsample_shape(max_size, total_size, shape, acq=False):
    if not acq:
        xy_axes_magnification = np.power(max_size / total_size, 1 / 3)
        slice_per_chunk = int(np.round(1 / xy_axes_magnification))
    else:
        slice_per_chunk = 1
        xy_axes_magnification = np.power(max_size / total_size, 1 / 2)
    num_chunks = 1 + len([i for i in range(slice_per_chunk, shape[2], slice_per_chunk)])

    target_image_shape = (int(xy_axes_magnification * shape[0]), int(xy_axes_magnification * shape[1]), num_chunks)
    return target_image_shape