from ccpi.viewer import viewer2D
from ccpi.viewer.utils import data_example

v = viewer2D()
# Load head data
data = data_example.HEAD.get()
v.setInputData(data)
v.startRenderLoop()
