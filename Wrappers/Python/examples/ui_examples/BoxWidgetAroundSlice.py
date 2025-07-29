import sys
from qtpy import QtWidgets
from ccpi.viewer import viewer2D, viewer3D
from SingleViewerCentralWidget import SingleViewerCenterWidget
from ccpi.viewer.widgets import cilviewerBoxWidget, cilviewerLineWidget

app = QtWidgets.QApplication(sys.argv)
# can change the behaviour by setting which viewer you want
# between viewer2D and viewer3D
window = SingleViewerCenterWidget(viewer=viewer2D)
line_widget = cilviewerLineWidget.CreateAtCoordOnXYPlane(window.frame.viewer, 'x', 5)
line_widget.On()
box_widget = cilviewerBoxWidget.CreateAroundSliceOnXYPlane(window.frame.viewer,
                                                           'y',
                                                           10,
                                                           width=1,
                                                           outline_color=(0, 0, 1))
box_widget.On()
window.frame.viewer.updatePipeline()

sys.exit(app.exec_())
