# coding=utf-8

import sys

from vtkmodules.vtkFiltersSources import vtkConeSource
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper, vtkRenderer
# load implementations for rendering and interaction factory classes
import vtkmodules.vtkRenderingOpenGL2
import vtkmodules.vtkInteractionStyle
from vtk.qt import QVTKRenderWindowInteractor as QVTK

# import QVTKRenderWindowInteractor as QVTK
QVTKRenderWindowInteractor = QVTK.QVTKRenderWindowInteractor

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QMainWindow
# if QVTK.PyQtImpl == 'PySide6':
#     from PySide6.QtCore import Qt
#     from PySide6.QtWidgets import QApplication, QMainWindow
# elif QVTK.PyQtImpl == 'PySide2':
#     from PySide2.QtCore import Qt
#     from PySide2.QtWidgets import QApplication, QMainWindow
# else:
#     from PySide.QtCore import Qt
#     from PySide.QtGui import QApplication, QMainWindow

from functools import partial


def handleResize(widget, re):
    print ("ResizeEvent", re.size(), re.oldSize())
    print (f"QVTKRenderWindowInteractor.GetSize(): {widget.GetSize()}")
    print (f"QVTKRenderWindowInteractor.size(): {widget.size()}")

def QVTKRenderWidgetConeExample(argv):
    """A simple example that uses the QVTKRenderWindowInteractor class."""
    # every QT app needs an app
    app = QApplication(['QVTKRenderWindowInteractor'])

    window = QMainWindow()
    

    # create the widget
    widget = QVTKRenderWindowInteractor(window)
    hr = partial(handleResize, widget)
    window.resizeEvent = hr
    
    window.setCentralWidget(widget)
    # if you don't want the 'q' key to exit comment this.
    widget.AddObserver("ExitEvent", lambda o, e, a=app: a.quit())

    ren = vtkRenderer()
    widget.GetRenderWindow().AddRenderer(ren)

    print("##### DPI", widget.GetRenderWindow().GetDPI())

    # window.resize(500,800)
    
    cone = vtkConeSource()
    cone.SetResolution(8)

    coneMapper = vtkPolyDataMapper()
    coneMapper.SetInputConnection(cone.GetOutputPort())

    coneActor = vtkActor()
    coneActor.SetMapper(coneMapper)

    ren.AddActor(coneActor)

    # show the widget
    window.show()

    widget.Initialize()

    widget.Start()

    # start event processing
    # Source: https://doc.qt.io/qtforpython/porting_from2.html
    # 'exec_' is deprecated and will be removed in the future.
    # Use 'exec' instead.
    try:
        app.exec()
    except AttributeError:
        app.exec_()

if __name__ == "__main__":
    QVTKRenderWidgetConeExample(sys.argv)