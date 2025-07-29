from vtk.util import colors

try:
    import matplotlib.pyplot as plt
except ImportError:
    # Add optional overload to allow plt.colormaps to be called without matplotlib
    from ccpi.viewer.utils import CILColorMaps

    class BackupColorMaps:

        @staticmethod
        def colormaps():
            return ["viridis", "plasma", "inferno", "magma"]

    plt = BackupColorMaps()


def color_scheme_list():
    """Return a list of color schemes for the color scheme dropdown menu."""
    initial_list = plt.colormaps()
    initial_list.insert(0, initial_list.pop(initial_list.index("viridis")))
    return initial_list


def background_color_list():
    """Return a list of background colors for the background color dropdown menu."""
    initial_list = dir(colors)
    color_list = [{
        "text": "Miles blue",
        "value": "cil_viewer_blue",
    }]

    initial_list.insert(0, initial_list.pop(initial_list.index("white")))
    initial_list.insert(1, initial_list.pop(initial_list.index("black")))

    for color in initial_list:
        if "_" in color:
            continue
        else:
            filtered_color = color
        filtered_color = filtered_color.capitalize()
        color_list.append({"text": filtered_color, "value": color})

    return color_list
