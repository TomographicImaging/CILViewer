import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from qtpy.QtCore import Qt, QEvent


class QCILRenderWindowInteractor(QVTKRenderWindowInteractor):
    '''
    A QVTKRenderWindowInteractor for Python and Qt. Uses a vtkGenericRenderWindowInteractor to handle the interactions.
    Use GetRenderWindow() to get the vtkRenderWindow. Create with the keyword stereo=1 in order to generate
    a stereo-capable window. Extends the QVTKRenderWindowInteractor to accept also ALT modifier.

    More info: https://docs.vtk.org/en/latest/api/python/vtkmodules/vtkmodules.qt.QVTKRenderWindowInteractor.html
    '''

    def __init__(self, parent=None, **kw):
        '''Constructor'''
        super(QCILRenderWindowInteractor, self).__init__(parent, **kw)
        self.__saveModifiers = self._QVTKRenderWindowInteractor__saveModifiers
        self.__saveX = self._QVTKRenderWindowInteractor__saveX
        self.__saveY = self._QVTKRenderWindowInteractor__saveY
        self.__saveButtons = self._QVTKRenderWindowInteractor__saveButtons
        self.__wheelDelta = self._QVTKRenderWindowInteractor__wheelDelta
        #print ("__saveModifiers  should be defined", self.__saveModifiers)

    def _GetAlt(self, ev):
        '''Get ALT key modifiers'''
        ctrl = shift = alt = False

        if hasattr(ev, 'modifiers'):
            if ev.modifiers() & Qt.AltModifier:
                alt = True
        else:
            if self.__saveModifiers & Qt.AltModifier:
                alt = True

        return alt

    def enterEvent(self, ev):
        '''Overload of enterEvent from base class to use _GetCtrlShiftAlt'''
        alt = self._GetAlt(ev)
        self._Iren.SetAltKey(alt)
        super().enterEvent(ev)

    def leaveEvent(self, ev):
        '''Overload of leaveEvent from base class to use _GetCtrlShiftAlt'''
        alt = self._GetAlt(ev)
        self._Iren.SetAltKey(alt)
        super().leaveEvent(ev)

    def mousePressEvent(self, ev):
        '''Overload of mousePressEvent from base class to use _GetCtrlShiftAlt'''
        alt = self._GetAlt(ev)
        self._Iren.SetAltKey(alt)
        super().mousePressEvent(ev)

    def mouseReleaseEvent(self, ev):
        '''Overload of mousePressEvent from base class to use _GetCtrlShiftAlt'''
        alt = self._GetAlt(ev)
        self._Iren.SetAltKey(alt)
        super().mouseReleaseEvent(ev)
        
    def mouseMoveEvent(self, ev):
        '''Overload of mouseMoveEvent from base class to use _GetCtrlShiftAlt'''
        alt = self._GetAlt(ev)
        self._Iren.SetAltKey(alt)
        super().mouseMoveEvent(ev)

