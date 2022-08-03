SLICE_ORIENTATION_XY = 2  # Z
SLICE_ORIENTATION_XZ = 1  # Y
SLICE_ORIENTATION_YZ = 0  # X

CONTROL_KEY = 8
SHIFT_KEY = 4
ALT_KEY = -128

SLICE_ACTOR = 'slice_actor'
OVERLAY_ACTOR = 'overlay_actor'
HISTOGRAM_ACTOR = 'histogram_actor'
HELP_ACTOR = 'help_actor'
CURSOR_ACTOR = 'cursor_actor'
CROSSHAIR_ACTOR = 'crosshair_actor'
LINEPLOT_ACTOR = 'lineplot_actor'
WIPE_ACTOR = 'wipe_actor'

from .CILViewer import CILViewer as viewer3D
from .CILViewer2D import CILViewer2D as viewer2D
from .CILViewer import CILInteractorStyle as istyle3D
from .CILViewer2D import CILInteractorStyle as istyle2D
from .version import version as dversion
