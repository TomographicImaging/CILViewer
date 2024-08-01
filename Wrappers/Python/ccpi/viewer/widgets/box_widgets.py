import vtk
from ccpi.viewer import SLICE_ORIENTATION_XY, SLICE_ORIENTATION_XZ, SLICE_ORIENTATION_YZ
from eqt.ui.SessionDialogs import WarningDialog


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
        data_extent = viewer.style.GetDataWorldExtent()
        print(viewer.style.GetVoxelsFromExtent(data_extent))
        voxel_max_world = viewer.style.GetVoxelsFromExtent(data_extent)[1]


        # Set the minimum world value
        world_image_min = (0, 0, 0)

        z_coords = [world_image_min[render_orientation], voxel_max_world[render_orientation]]

        if axis == 'x':
            # Displaying slice at fixed coord in X direction:
            x_coords = [coord, coord + width * spacing[0]]
            y_coords = [world_image_min[1], voxel_max_world[1]]

        else:
            # Displaying slice at fixed coord in Y direction:
            y_coords = [coord, coord + width * spacing[1]]
            x_coords = [world_image_min[0], voxel_max_world[0]]

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
        Given a position of the click, translates it into world coordinates.
        Gets the current render orientation.
        Gets the extent of the data in world coordiantes and its corresponding voxels. 
        Creates a warning dialog.
        Creates a 3D box around the clicked point, where the clicked point is the voxel min (lower value in all axes).
        Returns its extent in world coordinates, i.e., "box bounds". 
        Opens a warning dialog when the mouse click is outside the image.

        Parameters
        ----------
        viewer
            The 2D viewer where a projection of the 3D box will be displayed as a rectangle.
        position
            The event position in display coordinates, i.e., 3D coordinates of a mouse click on the image. 
        scale_factor
            Factor for scaling the size of the box to be smaller than the image shape.
        '''
        box_extent_world = [0, 0, 0, 0, 0, 0]

        orientation = viewer.style.GetSliceOrientation()

        coord = vtk.vtkCoordinate()
        coord.SetCoordinateSystemToDisplay()
        coord.SetValue(position[0], position[1])
        mouse_pos_world = coord.GetComputedWorldValue(viewer.style.GetRenderer())

        data_extent_world = viewer.style.GetDataWorldExtent()
        voxel_min_world, voxel_max_world = viewer.style.GetVoxelsFromExtent(data_extent_world)
        
        dialog = WarningDialog(None, message="Click inside the image.", window_title="Viewer Warning")

        box_voxel_min = [0,0,0]
        box_voxel_max = [0,0,0]
        i = [orientation, (orientation+1)%3, (orientation+2)%3]
        if voxel_min_world[i[1]] <= mouse_pos_world[i[1]]<= voxel_max_world[i[1]] and voxel_min_world[i[2]] <= mouse_pos_world[i[2]] <= voxel_max_world[i[2]]:

            box_voxel_min[i[0]] = voxel_min_world[i[0]]
            box_voxel_min[i[1]] = mouse_pos_world[i[1]]
            box_voxel_min[i[2]] = mouse_pos_world[i[2]]

            box_voxel_max[i[0]] = voxel_max_world[i[0]]
            box_voxel_max[i[1]] = cilviewerBoxWidget.GetTruncatedBoxCoord(box_voxel_min[i[1]], data_extent_world, i[1])
            box_voxel_max[i[2]] = cilviewerBoxWidget.GetTruncatedBoxCoord(box_voxel_min[i[2]], data_extent_world, i[2])

            box_extent_world = viewer.style.GetExtentFromVoxels(box_voxel_min, box_voxel_max)

        else:
            dialog.exec()

        return box_extent_world

    @staticmethod
    def GetTruncatedBoxCoord(start_pos, world_extent, axis_int, scale_factor=0.3):
        """
        Returns a coordinate for the edge of the box on axis [axis], scaled
        by factor [scale_factor], and truncated to make sure the box does not
        extend over the edge of the image shown.

        Parameters
        ----------
        start_pos: float
            Lower left corner value on specified axis
        world_extent:
            Array containing the extent of the world
        axis_int: int 0, 1, 2
            The axis to truncate on.
            SLICE_ORIENTATION_XY = 2  # Z
            SLICE_ORIENTATION_XZ = 1  # Y
            SLICE_ORIENTATION_YZ = 0  # X
        scale_factor: float
            The factor used to scale the length of the box, compared to the extent
            of the world on the given axis. 
            A scale factor of 1 would mean the length of the box on the given axis is 
            the same as the length of the image on that axis, unless the start position
            is greater than the minimum value on that axis, in which case, the box would
            be suitably truncated.
        """

        # get index for axis
        world_length = world_extent[2 * axis_int + 1] - world_extent[2 * axis_int]
        dist = world_length * scale_factor
        value = start_pos + dist

        # Check to make sure that it is within the image world.
        if value > world_extent[2 * axis_int + 1]:
            return world_extent[2 * axis_int + 1]
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
