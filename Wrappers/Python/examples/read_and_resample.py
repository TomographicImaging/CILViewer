import numpy as np
import vtk
import os
from ccpi.viewer import viewer2D
from ccpi.viewer.utils.conversion import Converter, parseNpyHeader, cilNumpyMETAImageWriter
from tqdm import tqdm
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
import functools
import tempfile
from ccpi.viewer.utils.conversion import cilNumpyResampleReader

if __name__ == "__main__":
    fname = os.path.abspath(r"E:\Documents\Dataset\CCPi\DVC\f000_crop\frame_000_f.npy")

    def progress(x, y):
        print("{:.0f}%".format(100 * x.GetProgress()))

    reader = cilNumpyResampleReader()
    reader.SetFileName(fname)
    reader.SetTargetSize(512**3)
    reader.AddObserver(vtk.vtkCommand.ProgressEvent, progress)
    reader.Update()
    resampled_image = reader.GetOutput()
    print("Spacing ", resampled_image.GetSpacing())

    v = viewer2D()
    v.setInputData(resampled_image)

    v.sliceActor.SetInterpolate(True)

    print("interpolated?", v.sliceActor.GetInterpolate())
    v.startRenderLoop()
