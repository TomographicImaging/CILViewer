import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor,\
        _qt_key_to_key_sym
from PyQt5.QtCore import Qt, QEvent

class QCILRenderWindowInteractor(QVTKRenderWindowInteractor):
    def __init__(self, parent=None, **kw):
        super(QCILRenderWindowInteractor, self).__init__(parent, **kw)
        self.__saveModifiers = self._QVTKRenderWindowInteractor__saveModifiers
        self.__saveX = self._QVTKRenderWindowInteractor__saveX
        self.__saveY = self._QVTKRenderWindowInteractor__saveY
        self.__saveButtons = self._QVTKRenderWindowInteractor__saveButtons
        self.__wheelDelta = self._QVTKRenderWindowInteractor__wheelDelta
        #print ("__saveModifiers  should be defined", self.__saveModifiers)
        
    def _GetCtrlShiftAlt(self, ev):
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
        ctrl, shift, alt = self._GetCtrlShiftAlt(ev)
        self._Iren.SetEventInformationFlipY(self.__saveX, self.__saveY,
                                            ctrl, shift, chr(0), 0, None)
        self._Iren.EnterEvent()

    def leaveEvent(self, ev):
        ctrl, shift , alt = self._GetCtrlShiftAlt(ev)
        self._Iren.SetEventInformationFlipY(self.__saveX, self.__saveY,
                                            ctrl, shift, chr(0), 0, None)
        self._Iren.LeaveEvent()

    def mousePressEvent(self, ev):
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

    

    def mouseReleaseEvent(self, ev):
        ctrl, shift = self._GetCtrlShift(ev)
        self._Iren.SetEventInformationFlipY(ev.x(), ev.y(),
                                            ctrl, shift, chr(0), 0, None)

        if self._ActiveButton == Qt.LeftButton:
            self._Iren.LeftButtonReleaseEvent()
        elif self._ActiveButton == Qt.RightButton:
            self._Iren.RightButtonReleaseEvent()
        elif self._ActiveButton == Qt.MidButton:
            self._Iren.MiddleButtonReleaseEvent()

    def mouseMoveEvent(self, ev):
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

    def keyPressEvent(self, ev):
        ctrl, shift = self._GetCtrlShift(ev)
        if ev.key() < 256:
            key = str(ev.text())
        else:
            key = chr(0)

        keySym = _qt_key_to_key_sym(ev.key())
        if shift and len(keySym) == 1 and keySym.isalpha():
            keySym = keySym.upper()

        self._Iren.SetEventInformationFlipY(self.__saveX, self.__saveY,
                                            ctrl, shift, key, 0, keySym)
        self._Iren.KeyPressEvent()
        self._Iren.CharEvent()

    def keyReleaseEvent(self, ev):
        ctrl, shift = self._GetCtrlShift(ev)
        if ev.key() < 256:
            key = chr(ev.key())
        else:
            key = chr(0)

        self._Iren.SetEventInformationFlipY(self.__saveX, self.__saveY,
                                            ctrl, shift, key, 0, None)
        self._Iren.KeyReleaseEvent()

    def wheelEvent(self, ev):
        if hasattr(ev, 'delta'):
            self.__wheelDelta += ev.delta()
        else:
            self.__wheelDelta += ev.angleDelta().y()

        if self.__wheelDelta >= 120:
            self._Iren.MouseWheelForwardEvent()
            self.__wheelDelta = 0
        elif self.__wheelDelta <= -120:
            self._Iren.MouseWheelBackwardEvent()
            self.__wheelDelta = 0
