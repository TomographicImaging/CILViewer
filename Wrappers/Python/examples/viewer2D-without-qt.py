from ccpi.viewer import viewer2D
from ccpi.viewer.utils import example_data

from ccpi.viewer.utils.conversion import Converter
import numpy as np

ndata = np.load("/Users/edoardo.pasca/Data/DVC_test_images/frame_010_f.npy")
data = Converter.numpy2vtkImage(ndata)

v = viewer2D(debug=False)
# Load head data
# data = example_data.HEAD.get()
v.setInputData(data)
v.startRenderLoop()
