import sys
import vtk
import os
from PyQt5 import QtCore, QtWidgets
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from ccpi.viewer.QCILRenderWindowInteractor import QCILRenderWindowInteractor
from ccpi.viewer import viewer2D, viewer3D
from ccpi.viewer.QCILViewerWidget import QCILViewerWidget, QCILDockableWidget
# Import linking class to join 2D and 3D viewers
import ccpi.viewer.viewerLinker as vlink


class FourLinkedViewersDockableWidget(QtWidgets.QMainWindow):

    def __init__(self, parent=None, reader=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        # self.resize(800,600)

        # create the dockable widgets with the viewer inside
        self.v00 = QCILDockableWidget(viewer=viewer2D, shape=(600, 600),
                                      title="X", interactorStyle=vlink.Linked2DInteractorStyle)
        self.v01 = QCILDockableWidget(viewer=viewer2D, shape=(600, 600),
                                      title="Y", interactorStyle=vlink.Linked2DInteractorStyle)
        self.v10 = QCILDockableWidget(viewer=viewer2D, shape=(600, 600),
                                      title="Z", interactorStyle=vlink.Linked2DInteractorStyle)
        self.v11 = QCILDockableWidget(viewer=viewer3D, shape=(600, 600),
                                      title="3D", interactorStyle=vlink.Linked3DInteractorStyle)

        # Create the viewer linkers
        viewerLinkers = self.linkedViewersSetup(
            self.v00, self.v01, self.v10, self.v11)

        for linker in viewerLinkers:
            linker.enable()

        self.viewerLinkers = viewerLinkers

        if reader is None:
            reader = vtk.vtkMetaImageReader()
            reader.SetFileName('head.mha')
        reader.Update()

        for el in [self.v00, self.v01, self.v10, self.v11]:
            el.viewer.setInputData(reader.GetOutput())
        # set slice orientation
        self.v00.viewer.setSliceOrientation('x')
        self.v01.viewer.setSliceOrientation('y')
        self.v10.viewer.setSliceOrientation('z')
        # disable reslicing by the user
        self.v00.viewer.style.reslicing_enabled = False
        self.v01.viewer.style.reslicing_enabled = False
        self.v10.viewer.style.reslicing_enabled = False

        # add to the GUI

        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,
                           self.v00, QtCore.Qt.Vertical)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,
                           self.v01, QtCore.Qt.Vertical)

        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,
                           self.v10, QtCore.Qt.Vertical)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,
                           self.v11, QtCore.Qt.Vertical)

        self.show()

    def linkedViewersSetup(self, *args):
        linked = [viewer for viewer in args]
        # link all combination of viewers
        #pairs = [(linked[0],linked[i]) for i in range(1, len(linked))]
        pairs = []
        for i in range(len(linked)):
            for j in range(len(linked)):
                if not i == j:
                    pairs.append((linked[i], linked[j]))

        linkers = []
        for pair in pairs:
            v2d = pair[0].viewer
            v3d = pair[1].viewer
            link2D3D = vlink.ViewerLinker(v2d, v3d)
            link2D3D.setLinkPan(False)
            link2D3D.setLinkZoom(False)
            link2D3D.setLinkWindowLevel(True)
            link2D3D.setLinkSlice(False)
            linkers.append(link2D3D)
        return linkers


if __name__ == "__main__":
    err = vtk.vtkFileOutputWindow()
    err.SetFileName("viewer.log")
    vtk.vtkOutputWindow.SetInstance(err)

    app = QtWidgets.QApplication(sys.argv)

    reader = vtk.vtkNIFTIImageReader()
    data_dir = os.path.abspath(
        'C:/Users/ofn77899/Documents/Projects/PETMR/Publications/2020RS_MCIR/cluster_test/recons')

    reader.SetFileName(os.path.join(
        data_dir, 'ungated_Reg-FGP_TV-alpha5.0_nGates1_nSubsets1_pdhg_wPrecond_gamma1.0_wAC_wNorm_wRands-riters100_noMotion_iters_39.nii'))
    window = FourLinkedViewersDockableWidget(reader=reader)

    sys.exit(app.exec_())
