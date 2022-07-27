import sys
from PySide2 import QtWidgets
from ccpi.viewer import viewer2D, viewer3D
from SingleViewerCentralWidget import SingleViewerCenterWidget
from ccpi.viewer.widgets.box_widgets import CreateBoxWidgetAroundSlice

app = QtWidgets.QApplication(sys.argv)
# can change the behaviour by setting which viewer you want
# between viewer2D and viewer3D
window = SingleViewerCenterWidget(viewer=viewer2D)
line_widget = CreateBoxWidgetAroundSlice(window.frame.viewer, 'horizontal', 5, width=0)
line_widget.On()
box_widget = CreateBoxWidgetAroundSlice(window.frame.viewer, 'vertical', 10, width=1, outline_color=(0, 0, 1))
box_widget.On()
window.frame.viewer.updatePipeline()

sys.exit(app.exec_())
