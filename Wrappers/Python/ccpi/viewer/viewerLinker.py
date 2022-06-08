# code largely copied from https://sourceforge.net/p/pyve/code/ci/master/tree/PyVE/components/viewer.py
# MIT licensed
from ccpi.viewer.CILViewer import CILInteractorStyle as CIL3DInteractorStyle
from ccpi.viewer.CILViewer2D import CILInteractorStyle as CIL2DInteractorStyle


class Linked3DInteractorStyle(CIL3DInteractorStyle):
    """
    Add attributes and methods needed to link two viewer together to the interactor style
    """

    def __init__(self, callback):
        CIL3DInteractorStyle.__init__(self, callback)

        self.LinkedInteractor = None
        self.LinkedEvent = 0

    def SetLinkedInteractor(self, iren):
        self.LinkedInteractor = iren

    def GetLinkedInteractor(self):
        return self.LinkedInteractor

    def GetLinkedEvent(self):
        return self.LinkedEvent

    def LinkedEventOn(self):
        self.LinkedEvent = 1

    def LinkedEventOff(self):
        self.LinkedEvent = 0


class Linked2DInteractorStyle(CIL2DInteractorStyle):
    """
    Add attributes and methods needed to link two viewer together to the interactor style
    """

    def __init__(self, callback):
        CIL2DInteractorStyle.__init__(self, callback)

        self.LinkedInteractor = None
        self.LinkedEvent = 0

    def SetLinkedInteractor(self, iren):
        self.LinkedInteractor = iren

    def GetLinkedInteractor(self):
        return self.LinkedInteractor

    def GetLinkedEvent(self):
        return self.LinkedEvent

    def LinkedEventOn(self):
        self.LinkedEvent = 1

    def LinkedEventOff(self):
        self.LinkedEvent = 0


class ViewerLinker():
    """
    This class sets up a link between two viewers. It offers methods
    for enabling and disabling the link, and setting up which events
    should be listened to.

    It makes use of the ViewerLinkObserver to establish a 'to' and 'from'
    connection.
    """

    def __init__(self, viewer1, viewer2):
        self._viewer1 = viewer1
        self._viewer2 = viewer2
        self._to = ViewerLinkObserver(viewer1, viewer2)
        self._from = ViewerLinkObserver(viewer2, viewer1)

    def __del__(self):
        self.disable()

    def enable(self):
        """
        Enable the viewer link
        """

        # Make sure the observers aren't added twice
        self.disable()

        self._observerToId = self._viewer1.getInteractor().AddObserver("AnyEvent", self._to)
        self._observerFromId = self._viewer2.getInteractor().AddObserver("AnyEvent", self._from)

    def disable(self):
        """
        Disable the viewer link
        """
        try:
            self._viewer1.getInteractor().RemoveObserver(self._observerToId)
            self._viewer2.getInteractor().RemoveObserver(self._observerFromId)
        except:
            # Already removed from observer list
            pass

    def setLinkZoom(self, linkZoom):
        """
        Boolean flag to set zoom linkage
        :param linkZoom: (boolean)
        """

        self._to.linkZoom = linkZoom
        self._from.linkZoom = linkZoom

    def setLinkPan(self, linkPan):
        """
        Boolean flag to set pan linkage
        :param linkPan: (boolean)
        """

        self._to.linkPan = linkPan
        self._from.linkPan = linkPan

    def setLinkPick(self, linkPick):
        """
        Boolean flag to set pick linkage
        :param linkPick: (boolean)
        """

        self._to.linkPick = linkPick
        self._from.linkPick = linkPick

    def setLinkWindowLevel(self, linkWindowLevel):
        """
        Boolean flag to set window level linkage
        :param linkWindowLevel: (boolean)
        """

        self._to.linkWindowLevel = linkWindowLevel
        self._from.linkWindowLevel = linkWindowLevel

    def setLinkSlice(self, linkSlice):
        """
        Boolean flag to set slice linkage
        :param linkSlice: (boolean)
        """

        self._to.linkSlice = linkSlice
        self._from.linkSlice = linkSlice

    def setLinkOrientation(self, linkOrientation):
        """
        Boolean flag to set slice orientation linkage
        :param linkOrientation: (boolean)
        """

        self._to.linkOrientation = linkOrientation
        self._from.linkOrientation = linkOrientation

    def setLinkInterpolation(self, linkInterpolation):
        """
        Boolean flag to set linkage of interpolation of slice actor
        :param linkInterpolation: (boolean)
        """

        self._to.linkInterpolation = linkInterpolation
        self._from.linkInterpolation = linkInterpolation


#################################
# ViewerLinkObserver
#################################
class ViewerLinkObserver():
    """
    This class passes events from a source viewer to a target. The user
    can pass it as an observer to the interactor of a viewer like this:

    linker = ViewerLinker(someViewer, someOtherViewer)
    someOtherViewer.getInteractor().AddObserver("AnyEvent", linker)

    It would be nice to listen to the vtkPyveInteractorStyle class, instead
    of the vktRenderWindowInteractor, so we can handle processed events like
    "WindowLevelEvent" or "StartSliceEvent". Unfortunately this is not
    possible, because in order to pass the event to the target viewer, the
    target interactor needs all the information the source interactor has,
    and invoking a "WindowLevelEvent" in the target vtkPyveInteractorStyle
    class will have no effect.

    This means we have to define the event handling again, as all we know are
    what mouse buttons are clicked etc, and whenever changes are made to the
    current handling, the same change should be made here.
    """

    def __init__(self, sourceViewer, targetViewer):
        self.sourceViewer = sourceViewer
        self.targetViewer = targetViewer
        self.sourceVtkViewer = self.sourceViewer
        self.targetVtkViewer = self.targetViewer
        self.sourceInteractor = self.sourceViewer.getInteractor()
        self.targetInteractor = self.targetViewer.getInteractor()
        self.sourceCamera = self.sourceVtkViewer.getRenderer().GetActiveCamera()
        self.targetCamera = self.targetVtkViewer.getRenderer().GetActiveCamera()
        self.linkZoom = True
        self.linkPan = True
        self.linkPick = True
        self.linkWindowLevel = True
        self.linkSlice = True
        self.linkOrientation = True
        self.linkInterpolation = True

    def __call__(self, interactor, event):
        """
        Handle the linked event.
        """
        sourceInteractorStyle = interactor.GetInteractorStyle()
        targetInteractorStyle = self.targetInteractor.GetInteractorStyle()
        state = sourceInteractorStyle.GetState()

        # Check for recursive event passing. Because two viewers can be linked
        # to each other, it is necessary to make sure one event isn't passed
        # back to the original viewer.
        try:
            if (self.targetInteractor.root):
                # Recursive
                return
        except:
            # The flag isn't set, so we can continue handling the current event.
            pass

        # We set a flag 'root' in the interactor, so we can check for recursive
        # event passing later on.
        interactor.root = True

        # We use this flag to store the result when we determine whether
        # we want to pass the current event.
        shouldPassEvent = True

        # Strange bug with middle button, only target viewer responds to
        # MiddleButtonPressEvent, but not to ReleaseEvent. Let's ignore it.
        if (event == "MiddleButtonPressEvent" or event == "MiddleButtonReleaseEvent"):
            shouldPassEvent = False

            # Zoom
        if (((event == "LeftButtonPressEvent") and interactor.GetAltKey() == 0 and interactor.GetControlKey() == 0
             and interactor.GetShiftKey() == 1) or state == 4 or state == 5):
            # Check if zooming is linked
            if (not self.linkZoom):
                # Not linked
                shouldPassEvent = False
            else:
                # Set current zoom
                if (event == "LeftButtonPressEvent"):
                    self.targetCamera.SetParallelScale(self.sourceCamera.GetParallelScale())

        # Pan
        if (((event == "LeftButtonPressEvent") and interactor.GetAltKey() == 0 and interactor.GetControlKey() == 1
             and interactor.GetShiftKey() == 0) or state == 2):
            # Check if panning is linked
            if (not self.linkPan):
                # Not linked
                shouldPassEvent = False

        # Pick
        if (((event == "LeftButtonPressEvent") and interactor.GetAltKey() == 0 and interactor.GetControlKey() == 0
             and interactor.GetShiftKey() == 0) or state == 1025):
            if isinstance(sourceInteractorStyle, Linked3DInteractorStyle):
                shouldPassEvent = False
            else:
                # Check if picking is linked
                if (not self.linkPick):
                    # Not linked
                    shouldPassEvent = False
                else:
                    # Set current slice to the picked voxel
                    # get pick position
                    pick_position = sourceInteractorStyle.last_picked_voxel
                    targetInteractorStyle.last_picked_voxel = pick_position[:]
                    sliceno = pick_position[self.targetViewer.sliceOrientation]
                    targetInteractorStyle.setActiveSlice(sliceno)
                    targetInteractorStyle.UpdatePipeline(True)
                    # the event has not been generated in the targetInteractor so it
                    # should not passed on to any linked interactors
                    shouldPassEvent = False

        # WindowLevel
        if (((event == "RightButtonPressEvent") and interactor.GetAltKey() == 1 and interactor.GetControlKey() == 0
             and interactor.GetShiftKey() == 0) or state == 1024):
            # Check if windowing/leveling is linked
            if (not self.linkWindowLevel):
                # Not linked
                shouldPassEvent = False
            else:
                # Set current window/level
                window = self.sourceViewer.getSliceColorWindow()
                level = self.sourceViewer.getSliceColorLevel()
                self.targetVtkViewer.setSliceColorWindowLevel(window, level)

        # Update window level on mouse move
        if (event == "MouseMoveEvent" and self.sourceViewer.event.isActive("WINDOW_LEVEL_EVENT")):

            if not self.linkWindowLevel:
                shouldPassEvent = False
            else:
                window = self.sourceViewer.getSliceColorWindow()
                level = self.sourceViewer.getSliceColorLevel()
                self.targetVtkViewer.setSliceColorWindowLevel(window, level)

        # Slice
        if (event == "MouseWheelForwardEvent" or event == "MouseWheelBackwardEvent" or state == 1026):
            # Check if slicing is linked
            if (not self.linkSlice):
                shouldPassEvent = False
            else:
                # Linked, check if orientation is the same
                if (self.sourceVtkViewer.getSliceOrientation() !=
                        self.targetVtkViewer.getSliceOrientation()):
                    shouldPassEvent = False

        # KeyPress and orientation
        if (event == "KeyPressEvent" or state == 1026):
            orientation_link_event = self.linkOrientation and (interactor.GetKeyCode() == "x"
                                                               or interactor.GetKeyCode() == "y"
                                                               or interactor.GetKeyCode() == "z")
            window_level_link_event = self.linkWindowLevel and (interactor.GetKeyCode() == "a"
                                                                or interactor.GetKeyCode() == "w")
            interpolation_link_event = self.linkInterpolation and interactor.GetKeyCode() == "i"
            if not (orientation_link_event or interpolation_link_event):
                shouldPassEvent = False

            if window_level_link_event:
                # Set current window/level
                window = self.sourceViewer.getSliceColorWindow()
                level = self.sourceViewer.getSliceColorLevel()
                self.targetVtkViewer.setSliceColorWindowLevel(window, level)

        # Check if event should be passed
        if (shouldPassEvent):
            # Pass event
            self.setupEvent(interactor, event)

            # Check if source interactor is already linked itself
            if (sourceInteractorStyle.GetLinkedEvent()):
                # Already linked, pass source interactor
                targetInteractorStyle.SetLinkedInteractor(sourceInteractorStyle.GetLinkedInteractor())
            else:
                # Not linked, this is the source interactor
                targetInteractorStyle.SetLinkedInteractor(interactor)

            # Invoke event in target interactor.
            self.targetInteractor.InvokeEvent(event)

            # Set event back to normal
            targetInteractorStyle.LinkedEventOff()
            targetInteractorStyle.SetLinkedInteractor(None)

        interactor.root = False

    def setupEvent(self, interactor, event):
        """
        Set all necessary event information in target interactor.
        """
        # Set all required event information.
        self.targetInteractor.SetEventPosition(interactor.GetEventPosition())
        self.targetInteractor.SetAltKey(interactor.GetAltKey())
        self.targetInteractor.SetControlKey(interactor.GetControlKey())
        self.targetInteractor.SetShiftKey(interactor.GetShiftKey())
        self.targetInteractor.SetKeyCode(interactor.GetKeyCode())
        self.targetInteractor.SetRepeatCount(interactor.GetRepeatCount())
        self.targetInteractor.SetKeySym(interactor.GetKeySym())

        # print (type(self.targetInteractor.GetInteractorStyle()))
        # Mark the event as linked
        self.targetInteractor.GetInteractorStyle().LinkedEventOn()
