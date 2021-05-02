import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor,\
        _qt_key_to_key_sym
from PySide2.QtCore import Qt, QEvent

class QCILRenderWindowInteractor(QVTKRenderWindowInteractor):
    '''Extends the QVTKRenderWindowInteractor to accept also ALT modifier'''
    def __init__(self, parent=None, **kw):
        '''Constructor'''
        super(QCILRenderWindowInteractor, self).__init__(parent, **kw)
        self.__saveModifiers = self._QVTKRenderWindowInteractor__saveModifiers
        self.__saveX = self._QVTKRenderWindowInteractor__saveX
        self.__saveY = self._QVTKRenderWindowInteractor__saveY
        self.__saveButtons = self._QVTKRenderWindowInteractor__saveButtons
        self.__wheelDelta = self._QVTKRenderWindowInteractor__wheelDelta
        #print ("__saveModifiers  should be defined", self.__saveModifiers)
        
    def _GetCtrlShiftAlt(self, ev):
        '''Get CTRL SHIFT ALT key modifiers'''
        ctrl = shift = alt = False

        if hasattr(ev, 'modifiers'):
            
            if ev.modifiers() & Qt.ShiftModifier:
                shift = True
            if ev.modifiers() & Qt.ControlModifier:
                ctrl = True
            if ev.modifiers() & Qt.AltModifier:
                alt = True
        else:
            if self.__saveModifiers & Qt.ShiftModifier:
                shift = True
            if self.__saveModifiers & Qt.ControlModifier:
                ctrl = True
            if self.__saveModifiers & Qt.AltModifier:
                alt = True

        return ctrl, shift, alt
    def enterEvent(self, ev):
        '''Overload of enterEvent from base class to use _GetCtrlShiftAlt'''
        ctrl, shift, alt = self._GetCtrlShiftAlt(ev)
        self._Iren.SetEventInformationFlipY(self.__saveX, self.__saveY,
                                            ctrl, shift, chr(0), 0, None)
        self._Iren.EnterEvent()

    def leaveEvent(self, ev):
        '''Overload of leaveEvent from base class to use _GetCtrlShiftAlt'''
        ctrl, shift , alt = self._GetCtrlShiftAlt(ev)
        self._Iren.SetEventInformationFlipY(self.__saveX, self.__saveY,
                                            ctrl, shift, chr(0), 0, None)
        self._Iren.LeaveEvent()

    def mousePressEvent(self, ev):
        '''Overload of mousePressEvent from base class to use _GetCtrlShiftAlt'''
        ctrl, shift, alt  = self._GetCtrlShiftAlt(ev)
        repeat = 0
        if ev.type() == QEvent.MouseButtonDblClick:
            repeat = 1
        self._Iren.SetEventInformationFlipY(ev.x(), ev.y(),
                                            ctrl, shift, chr(0), repeat, None)
        self._Iren.SetAltKey(alt)
        self._Iren.SetShiftKey(shift)
        self._Iren.SetControlKey(ctrl)
                
        self._ActiveButton = ev.button()

        if self._ActiveButton == Qt.LeftButton:
            self._Iren.LeftButtonPressEvent()
        elif self._ActiveButton == Qt.RightButton:
            self._Iren.RightButtonPressEvent()
        elif self._ActiveButton == Qt.MidButton:
            self._Iren.MiddleButtonPressEvent()

    def mouseMoveEvent(self, ev):
        '''Overload of mouseMoveEvent from base class to use _GetCtrlShiftAlt'''
        self.__saveModifiers = ev.modifiers()
        self.__saveButtons = ev.buttons()
        self.__saveX = ev.x()
        self.__saveY = ev.y()

        #ctrl, shift = self._GetCtrlShift(ev)
        ctrl, shift, alt  = self._GetCtrlShiftAlt(ev)
        self._Iren.SetEventInformationFlipY(ev.x(), ev.y(),
                                            ctrl, shift, chr(0), 0, None)
        self._Iren.SetAltKey(alt)
        self._Iren.MouseMoveEvent()
