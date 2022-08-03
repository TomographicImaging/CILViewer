import vtk
from ccpi.viewer import SLICE_ORIENTATION_XY, SLICE_ORIENTATION_XZ, SLICE_ORIENTATION_YZ


class cilviewerBoxWidget():

    @staticmethod
    def CreateFixed(viewer, outline_colour=(0, 1, 0)):
        '''
        Creates a vtkBoxWidget which the user can't move
        
        Parameters
        ----------
        viewer
            The viewer that the box widget will later be working on.
            The interactor for the widget will be set to this viewer's
            interactor.
        outline_color
            The color of the outline of the box widget

        Returns
        -------
        widget: vtk.vtkBoxWidget
        '''
        widget = vtk.vtkBoxWidget()
        widget.SetInteractor(viewer.iren)
        widget.HandlesOff()
        widget.TranslationEnabledOff()
        widget.RotationEnabledOff()
        widget.GetOutlineProperty().SetColor(outline_colour)
        widget.OutlineCursorWiresOff()
        widget.SetPlaceFactor(1)
        widget.KeyPressActivationOff()
        widget.ScalingEnabledOff()
        return widget

    @staticmethod
    def CreateMoveable(viewer, outline_colour=(0, 1, 0)):
        '''
        Creates a vtkBoxWidget which the user can move

        Parameters
        ----------
        viewer
            The viewer that the box widget will later be working on.
            The interactor for the widget will be set to this viewer's
            interactor.
        outline_color
            The color of the outline of the box widget

        Returns
        -------
        widget: vtk.vtkBoxWidget
        '''
        widget = vtk.vtkBoxWidget()
        widget.SetInteractor(viewer.iren)
        widget.HandlesOn()
        widget.TranslationEnabledOn()
        widget.RotationEnabledOff()
        widget.GetOutlineProperty().SetColor(outline_colour)
        widget.OutlineCursorWiresOff()
        widget.SetPlaceFactor(1)
        widget.KeyPressActivationOff()
        return widget

    @staticmethod
    def CreateAroundSliceOnXYPlane(viewer,
                                   axis='x',
                                   coord=0,
                                   outline_color=(1., 0., 0.),
                                   width=1,
                                   widget_name='slice_outline_widget'):
        '''
        Creates a border in [viewer], around a slice with number [coord] on
        the [axis] axis. This border is a vtkBoxWidget.
        This appears as an overlay, so appears on every projection.
        E.g. if orientation = 'y', coord = 5, width=1 then it creates a
        border around the voxels with y value of 5.
        width controls the width of the box, but it always starts at [coord].
        E.g. if orientation = 'y', coord = 5, width = 5 then it creates a
        border around the voxels with y values of 5-9.

        Note, setting width=0 creates a line rather than a box

        Parameters
        ----------
        viewer: viewer2D or viewer3D
            A viewer upon which the border will be displayed
        axis: {'x', 'y'}
            Which axis the slice is on
        coord: int
            The coordinate of the slice in world coords
        outline_color: tuple
            colour of the border
        width: float
            The width of the border. The border starts from the bound of the
            slice with number coord.
        widget_name: str
            The name to associate the border widget with in the viewer.
        '''

        widget = cilviewerBoxWidget.CreateFixed(viewer, outline_color)
        coords = cilviewerBoxWidget.GetCoordsForBoxWidgetAroundSlice(viewer, axis, coord, width)
        widget.PlaceWidget(coords)
        viewer.addWidgetReference(widget, widget_name)
        return widget

    @staticmethod
    def GetCoordsForBoxWidgetAroundSlice(viewer, axis='x', coord=0, width=1):
        '''
        Generate coordinates for positioning BoxWidget around slice
        
        Parameters
        ----------
        viewer: viewer2D or viewer3D
            A viewer upon which the border will be displayed
        orientation: {'x', 'y'}
            Which axis the slice is on
        coord: int
            The coordinate of the slice in world coords
        width: float
            The width of the border. The border starts from the bound of the
            slice with number coord.
        
        '''

        # Only makes sense to do this on the Z axis:
        render_orientation = SLICE_ORIENTATION_XY
        try:
            viewer.setSliceOrientation(render_orientation)
        except:  # method doesn't exist on 3D viewer
            pass

        spacing = viewer.img3D.GetSpacing()

        # Get maximum extents of the image in world coords
        world_image_max = viewer.style.GetImageWorldExtent()

        # Set the minimum world value
        world_image_min = (0, 0, 0)

        z_coords = [world_image_min[render_orientation], world_image_max[render_orientation]]

        if axis == 'x':
            # Displaying slice at fixed coord in X direction:
            x_coords = [coord, coord + width * spacing[0]]
            y_coords = [world_image_min[1], world_image_max[1]]

        else:
            # Displaying slice at fixed coord in Y direction:
            y_coords = [coord, coord + width * spacing[1]]
            x_coords = [world_image_min[0], world_image_max[0]]

        coords = x_coords + y_coords + z_coords

        return coords

    @staticmethod
    def CreateMoveableAtEventPosition(viewer, position, widget_name, outline_colour=(0, 1, 0), scale_factor=0.3):
        ''' 
        Place a moveable box widget on the viewer at the event position.
        Parameters
        ----------
        viewer
            The 2D viewer that the box will be displayed on
        position
            The event position
        widget_name
            The name the reference to the widget will be stored as
        outline_color
            The outline color of the box widget
        scale_factor
            Factor for scaling the size of the box
        '''
        # ROI Widget
        widget = cilviewerBoxWidget.CreateMoveable(viewer, outline_colour)
        coords = cilviewerBoxWidget.GetBoxBoundsFromEventPosition(viewer, position, scale_factor)
        # Set widget placement and make visible
        widget.PlaceWidget(coords)
        widget.On()
        viewer.addWidgetReference(widget, widget_name)
        return widget

    @staticmethod
    def GetBoxBoundsFromEventPosition(viewer, position, scale_factor=0.3):
        ''' 
        Get the coordinates for the bounds of a box from the event position

        Parameters
        ----------
        viewer
            The 2D viewer that the box will be displayed on
        position
            The event position
        scale_factor
            Factor for scaling the size of the box
        '''
        # Current render orientation
        orientation = viewer.style.GetSliceOrientation()

        # Translate the mouse click display coordinates into world coordinates
        coord = vtk.vtkCoordinate()
        coord.SetCoordinateSystemToDisplay()
        coord.SetValue(position[0], position[1])
        world_mouse_pos = coord.GetComputedWorldValue(viewer.style.GetRenderer())

        # Get maximum extents of the image in world coords
        world_image_max = viewer.style.GetImageWorldExtent()

        # Set the minimum world value
        world_image_min = (0, 0, 0)

        # Initialise the box position in format [xmin, xmax, ymin, ymax,...]
        box_pos = [0, 0, 0, 0, 0, 0]

        # place the mouse click as bottom left in current orientation
        if orientation == SLICE_ORIENTATION_XY:
            # Looking along z
            # Lower left is xmin, ymin
            box_pos[0] = world_mouse_pos[0]
            box_pos[2] = world_mouse_pos[1]

            # Set top right point
            # Top right is xmax, ymax
            box_pos[1] = cilviewerBoxWidget.GetTruncatedBoxCoord(box_pos[0], world_image_max, "x", scale_factor)
            box_pos[3] = cilviewerBoxWidget.GetTruncatedBoxCoord(box_pos[2], world_image_max, "y", scale_factor)

            # Set the scroll axis to maximum extent eg. min-max
            # zmin, zmax
            box_pos[4] = world_image_min[orientation]
            box_pos[5] = world_image_max[orientation]

        elif orientation == SLICE_ORIENTATION_XZ:
            # Looking along y
            # Lower left is xmin, zmin
            box_pos[0] = world_mouse_pos[0]
            box_pos[4] = world_mouse_pos[2]

            # Set top right point.
            # Top right is xmax, zmax
            box_pos[1] = cilviewerBoxWidget.GetTruncatedBoxCoord(box_pos[0], world_image_max, "x")
            box_pos[5] = cilviewerBoxWidget.GetTruncatedBoxCoord(box_pos[4], world_image_max, "z")

            # Set the scroll axis to maximum extent eg. min-max
            # ymin, ymax
            box_pos[2] = world_image_min[orientation]
            box_pos[3] = world_image_max[orientation]

        else:
            # orientation == 0
            # Looking along x
            # Lower left is ymin, zmin
            box_pos[2] = world_mouse_pos[1]
            box_pos[4] = world_mouse_pos[2]

            # Set top right point
            # Top right is ymax, zmax
            box_pos[3] = cilviewerBoxWidget.GetTruncatedBoxCoord(box_pos[2], world_image_max, "y")
            box_pos[5] = cilviewerBoxWidget.GetTruncatedBoxCoord(box_pos[4], world_image_max, "z")

            # Set the scroll axis to maximum extent eg. min-max
            # xmin, xmax
            box_pos[0] = world_image_min[orientation]
            box_pos[1] = world_image_max[orientation]

        return box_pos

    @staticmethod
    def GetTruncatedBoxCoord(start_pos, world_max_array, axis, scale_factor=0.3):
        """
        Make sure that the value for the upper corner of the box is within the world extent.

        Parameters
        ----------
        start_pos: 
            Lower left corner value on specified axis
        world_max_array:
            Array containing (x,y,z) of the maximum extent of the world
        axis: str, {'x', 'y', 'z'}
            The axis to truncate on.
        scale_factor:
            The start position + a percentage of the world truncated to the edges of the world
        """

        # get index for axis
        axis_dict = {"x": SLICE_ORIENTATION_YZ, "y": SLICE_ORIENTATION_XZ, "z": SLICE_ORIENTATION_XY}
        axis_int = axis_dict[axis]

        # Create the upper right coordinate point with scale offset
        value = start_pos + world_max_array[axis_int] * scale_factor

        # Check to make sure that it is within the image world.
        if value > world_max_array[axis_int]:
            return world_max_array[axis_int]
        else:
            return value


class cilviewerLineWidget():

    @staticmethod
    def CreateAtCoordOnXYPlane(viewer, axis='x', coord=0, outline_color=(1., 0., 0.), widget_name='slice_line_widget'):
        '''
            Creates a line in [viewer], at [coord] on the
            the [axis] axis. This line is made using a vtkBoxWidget.
            When created, the direction of view is forced to be SLICE_ORIENTATION_XY,
            so only the X or Y axis can be chosen.
            This appears as an overlay, so appears on every projection.
            E.g. if orientation = 'y', coord = 5, then it creates a
            line with y value of 5.

            Parameters
            ----------
            viewer: viewer2D or viewer3D
                A viewer upon which the border will be displayed
            axis: {'x', 'y'}
                Which axis the slice is on
            coord: int
                The coordinate of the slice in world coords
            outline_color: tuple
                colour of the border
            widget_name: str
                The name to associate the border widget with in the viewer.
            '''

        widget = cilviewerBoxWidget.CreateAroundSliceOnXYPlane(viewer,
                                                               axis,
                                                               coord,
                                                               outline_color,
                                                               width=0,
                                                               widget_name=widget_name)
        return widget
