from ccpi.viewer import viewer2D
from ccpi.viewer.utils import example_data


v = viewer2D(debug=False)
# Load head data
data = example_data.HEAD.get()
v.setInputData(data)
v.startRenderLoop()
