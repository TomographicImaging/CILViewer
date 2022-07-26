import vtk

def CreateViewerSliceBorder(viewer, orientation='horizontal', coord=0, color=(1., 0., 0.), width=1, widget_name='slice_outline_widget', ):
    ''' Creates a border in [viewer], around a slice with number [coord] in
        the [orientation] plane.
        This appears as an overlay, so appears on every projection.
        E.g. if orientation = 'vertical', coord = 5, width=1 then it creates a
        border around the voxels with vertical value of 5.
        width controls the width of the box, but it always starts at [coord].
        E.g. if orientation = 'vertical', coord = 5, width = 5 then it creates a
        border around the voxels with vertical values of 5-9.

    Parameters
    ----------
    viewer: viewer2D or viewer3D
        A viewer upon which the border will be displayed
    orientation: {'horizontal', 'vertical'}
        Which axis the slice is on
    coord: int
        The coordinate of the slice
    color: tuple
        colour of the border
    width: float
        The width of the border. The border starts from the bound of the
        slice with number coord.
    widget_name: str
        The name to associate the border widget with in the viewer.

    '''
    extent = viewer.img3D.GetExtent()
    spac = viewer.img3D.GetSpacing()

    if orientation == "vertical":
        x_length = extent[1]
        pos1 = [0, coord] 
        pos2 = [x_length, coord+width]
    else:
        y_length = extent[3]
        pos1 = [coord, y_length] 
        pos2 = [coord + width, 0]


    CreateViewerOverlayBorder(viewer, pos1, pos2, color, widget_name)



def CreateViewerOverlayBorder(viewer, pos1, pos2,
                     color=(1., 0., 0.), widget_name='box_widget'): 
    ''' 
    Creates a border in [viewer], with the two alternate corner
    positions at [pos1], [pos2]
    This appears as an overlay, so appears on every projection.

    Parameters
    ----------
    viewer: viewer2D or viewer3D
        A viewer upon which the border will be displayed
    pos1: tuple
        coordinates of lower left corner of the border widget (in image coordinates)
    pos2: tuple
        coordinates of top right corner of the border widget (in image coordinates)
    color: tuple
        colour of the border
    widget_name: str
        The name to associate the border widget with in the viewer.
    '''

    if hasattr(viewer, 'widgets'):
        box_widget = widget_name in viewer.widgets
    else:
        viewer.widgets={}
        box_widget = False

    if not box_widget:
        borderWidget = vtk.vtkBorderWidget();
        representation = vtk.vtkBorderRepresentation()
        borderWidget.SetRepresentation(representation)
        #borderWidget.CreateDefaultRepresentation()
        borderWidget.SetResizable(False)
        borderWidget.SetProcessEvents(False)
        borderWidget.SelectableOff()
        borderWidget.SetInteractor(viewer.iren)
        viewer.widgets[widget_name] = borderWidget

    else:
        borderWidget = viewer.widgets[widget_name]

    # coord conversion
    # pos1 = list(pos1)
    # pos2 = list(pos2)
    # pos1.append(0)
    # pos2.append(0)
    # print("POS 1")
    # print(pos1)
    
    # pos1 = viewer.style.image2world(pos1)[:2]
    # print("POS 2")
    # print(pos2)
    # pos2 = viewer.style.image2world(pos2)[:2]

    # borderWidget.GetBorderRepresentation().SetPosition((0.05,0.05))
    # borderWidget.GetBorderRepresentation().SetPosition2((1,1))
    # borderWidget.GetBorderRepresentation().GetBorderProperty().SetColor(color)
    # print( borderWidget.GetBorderRepresentation().GetPosition() , borderWidget.GetBorderRepresentation().GetPosition2())
    # print( borderWidget.GetBorderRepresentation().GetPosition() , borderWidget.GetBorderRepresentation().GetPosition2())
    print(borderWidget.GetBorderRepresentation().GetBounds())
    borderWidget.On()

    viewer.style.UpdatePipeline()