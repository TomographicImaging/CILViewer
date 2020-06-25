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
    fname = os.path.abspath(r"D:\Documents\Dataset\CCPi\DVC\f000_crop\frame_000_f.npy")
    
    def progress(x,y):
        print ("{:.0f}%".format(100*x.GetProgress()))

    reader = cilNumpyResampleReader()
    reader.SetFileName(fname)
    reader.SetTargetShape((512,512,512))
    reader.AddObserver(vtk.vtkCommand.ProgressEvent, progress)
    reader.Update()
    resampled_image = reader.GetOutput()
    print ("Spacing ", resampled_image.GetSpacing())
    
    v = viewer2D()
    v.setInputData(resampled_image)
    # v.setInputData2(vtk_not_resampled)

    # lut = v.lut2
    # lut.SetNumberOfColors(16)
    # lut.SetHueRange(.2,.8)
    # lut.SetSaturationRange(.1, .6)
    # lut.SetValueRange(100, 200)
    # lut.SetAlphaRange(0,0.5)
    # lut.Build()
    # v.sliceActor2.Update()

    v.sliceActor.SetInterpolate(True)

    print("interpolated?" , v.sliceActor.GetInterpolate())
    v.startRenderLoop()

