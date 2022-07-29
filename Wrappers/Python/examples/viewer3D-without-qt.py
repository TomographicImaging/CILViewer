from ccpi.viewer import viewer3D
from ccpi.viewer.utils import example_data

v = viewer3D()
# Load head data
data = example_data.HEAD.get()
v.setInputData(data)
v.startRenderLoop()