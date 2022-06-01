from ccpi.viewer import viewer3D
from ccpi.viewer.utils import data_example

v = viewer3D()
# Load head data
data = data_example.HEAD.get()
v.setInputData(data)
v.startRenderLoop()