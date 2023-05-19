from eqt.ui.UIFormWidget import FormDockWidget
from PySide2.QtWidgets import QComboBox, QLabel
from ccpi.viewer.CILViewer import CILViewer
from ccpi.viewer.CILViewer2D import CILViewer2D

class ViewerCoordsDockWidget(FormDockWidget):
    ''' This is the dockwidget which
    shows the original and downsampled image
    size and the user can select whether coordinates
    are displayed in system of original or downsampled image'''

    def __init__(self, parent, viewers=None):
        '''
        Parameters
        ----------
        parent : QWidget
            The parent widget.
        viewers : list of CILViewer2D and/or CILViewer instances, default = None
            The viewers which this dock widget will display information for.
        '''
        super(ViewerCoordsDockWidget, self).__init__(parent)

        self.setViewers(viewers)

        form = self.widget()

        viewer_coords_widgets = {}

        viewer_coords_widgets['image'] = QLabel()
        viewer_coords_widgets['image'].setText("Display image: ")

        viewer_coords_widgets['image_combobox'] = QComboBox()
        viewer_coords_widgets['image_combobox'].setEnabled(False)
        form.addWidget(viewer_coords_widgets['image_combobox'], viewer_coords_widgets['image'], 'image')

        viewer_coords_widgets['coords_info'] = QLabel()
        viewer_coords_widgets['coords_info'].setText(
            "The viewer displays a downsampled image for visualisation purposes: ")
        viewer_coords_widgets['coords_info'].setVisible(False)

        form.addSpanningWidget(viewer_coords_widgets['coords_info'], 'coords_info')

        form.addWidget(QLabel(""), QLabel("Loaded Image Size: "), 'loaded_image_dims')

        viewer_coords_widgets['displayed_image_dims_label'] = QLabel()
        viewer_coords_widgets['displayed_image_dims_label'].setText("Displayed Image Size: ")
        viewer_coords_widgets['displayed_image_dims_label'].setVisible(False)

        viewer_coords_widgets['displayed_image_dims_field'] = QLabel()
        viewer_coords_widgets['displayed_image_dims_field'].setText("")
        viewer_coords_widgets['displayed_image_dims_field'].setVisible(False)

        form.addWidget(viewer_coords_widgets['displayed_image_dims_field'],
                       viewer_coords_widgets['displayed_image_dims_label'], 'displayed_image_dims')

        viewer_coords_widgets['coords'] = QLabel()
        viewer_coords_widgets['coords'].setText("Display viewer coordinates in: ")

        viewer_coords_widgets['coords_combo'] = QComboBox()
        viewer_coords_widgets['coords_combo'].addItems(["Loaded Image", "Downsampled Image"])
        viewer_coords_widgets['coords_combo'].setEnabled(False)
        form.addWidget(viewer_coords_widgets['coords_combo'], viewer_coords_widgets['coords'], 'coords_combo')

        viewer_coords_widgets['coords_warning'] = QLabel()
        viewer_coords_widgets['coords_warning'].setText("Warning: These coordinates are approximate.")
        viewer_coords_widgets['coords_warning'].setVisible(False)

        form.addSpanningWidget(viewer_coords_widgets['coords_warning'], 'coords_warning')

    @property
    def viewers(self):
        ''' Get the viewers which this dock widget will display information for.
        
        Returns
        -------
        list of CILViewer2D and/or CILViewer3D instances
            The viewers which this dock widget will display information for.'''
        return self._viewers
    
    @viewers.setter
    def viewers(self, viewers):
        '''
        Set the viewers which this dock widget will display information for.

        Parameters
        ----------
        viewers : list of CILViewer2D and/or CILViewer instances
            The viewers which this dock widget will display information for.
        '''
        if viewers is not None:
            if not isinstance(viewers, list):
                viewers = [viewers]
            for viewer in viewers:
                if not isinstance(viewer, (CILViewer2D, CILViewer)):
                    raise TypeError("viewers must be a list of CILViewer2D and/or CILViewer instances")
        self._viewers = viewers


    def setViewers(self, viewers):
        ''' Set the viewers which this dock widget will display information for.

        Parameters
        ----------
        viewers : list of CILViewer2D and/or CILViewer instances
            The viewers which this dock widget will display information for.
        '''
        self.viewers = viewers


    def getViewers(self):
        ''' Get the viewers which this dock widget will display information for.
        
        Returns
        -------
        list of CILViewer2D and/or CILViewer instances
            The viewers which this dock widget will display information for.'''
        return self.viewers
