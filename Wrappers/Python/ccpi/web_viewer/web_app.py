#
#   Copyright 2022 STFC, United Kingdom Research and Innovation
#
#   Author 2022 Samuel Jones
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import getopt
import os
import sys

from trame import state

from ccpi.web_viewer.trame_viewer2D import TrameViewer2D
from ccpi.web_viewer.trame_viewer3D import TrameViewer3D

TRAME_VIEWER = None
VIEWER_2D = False


def arg_parser():
    """
    Parse the passed arguments to the current
    :return:
    """
    help_string = "web_app.py [optional args: -h, -d] <data_files>\n" \
                  "Args:\n" \
                  "-h: Show this help and exit the program\n" \
                  "-d, --2D: Use the 2D viewer instead of the 3D viewer, the default is to just use the 3D viewer."
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd", ["2D"])
    except getopt.GetoptError:
        print(help_string)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(help_string)
        elif opt in ("-d", "--2D"):
            global VIEWER_2D
            VIEWER_2D = True
    return data_finder()

def data_finder():
    """
    Finds all files that are needed to be passed to the TrameViewer that in a list that is digestible, using the passed args.
    :return: list, of full file paths of data in the given directory parameter
    """
    data_files = []
    for index, arg in enumerate(sys.argv):
        if index == 0 or arg[0] == '-':
            # this is the python script in index 0 and not a passed arg
            continue
        if os.path.isfile(arg):
            data_files.append(arg)
        elif os.path.isdir(arg):
            files_in_dir = os.listdir(arg)
            for file in files_in_dir:
                data_files.append(os.path.join(arg, file))
        else:
            print(f"This arg: {arg} is not a valid file or directory. Assuming it is for trame.")
    return data_files


def main() -> int:
    """
    Create the main class and run the TrameViewer
    :return: int, exit code for the program
    """
    data_files = arg_parser()
    global TRAME_VIEWER
    if not VIEWER_2D:
        TRAME_VIEWER = TrameViewer3D(data_files)
        TRAME_VIEWER.start()
    else:
        TRAME_VIEWER = TrameViewer2D(data_files)
        TRAME_VIEWER.start()
    return 0


@state.change("slice")
def update_slice(**kwargs):
    TRAME_VIEWER.change_slice_number(kwargs["slice"])


@state.change("orientation")
def change_orientation(**kwargs):
    if "orientation" in kwargs:
        orientation = kwargs["orientation"]
        if orientation is not int:
            orientation = int(orientation)
        TRAME_VIEWER.switch_to_orientation(int(orientation))


@state.change("opacity")
def change_opacity_mapping(**kwargs):
    if "opacity" in kwargs:
        TRAME_VIEWER.set_opacity_mapping(kwargs["opacity"])


@state.change("file_name")
def change_model(**kwargs):
    TRAME_VIEWER.load_file(kwargs['file_name'], windowing_method=kwargs['opacity'])


@state.change("color_map")
def change_color_map(**kwargs):
    TRAME_VIEWER.change_color_map(kwargs['color_map'])


@state.change("windowing")
def change_windowing(**kwargs):
    TRAME_VIEWER.change_windowing(kwargs["windowing"][0], kwargs["windowing"][1], windowing_method=kwargs['opacity'])


@state.change("coloring")
def change_coloring(**kwargs):
    TRAME_VIEWER.change_coloring(kwargs["coloring"][0], kwargs["coloring"][1])


@state.change("slice_window")
def change_slice_window(**kwargs):
    TRAME_VIEWER.change_slice_window(kwargs["slice_window"])


@state.change("slice_level")
def change_slice_level(**kwargs):
    TRAME_VIEWER.change_slice_level(kwargs["slice_level"])


@state.change("slice_window_range")
def change_slice_window_level(**kwargs):
    min_window = kwargs["slice_window_range"][0]
    max_window = kwargs["slice_window_range"][1]
    level = (max_window + min_window) / 2
    window = (max_window - min_window)
    TRAME_VIEWER.change_slice_window_range(window=window, level=level)


@state.change("slice_detailed_sliders")
def change_slice_detailed_sliders(**kwargs):
    TRAME_VIEWER.change_window_level_detail_sliders(kwargs["slice_detailed_sliders"])


@state.change("slice_visibility")
def change_slice_visibility(**kwargs):
    TRAME_VIEWER.change_slice_visibility(kwargs["slice_visibility"])


@state.change("volume_visibility")
def change_volume_visibility(**kwargs):
    TRAME_VIEWER.change_volume_visibility(kwargs["volume_visibility"])


@state.change("background_color")
def change_background_color(**kwargs):
    TRAME_VIEWER.change_background_color(kwargs["background_color"])


@state.change("toggle_clipping")
def change_clipping(**kwargs):
    TRAME_VIEWER.change_clipping(kwargs["toggle_clipping"])


@state.change("toggle_tracing")
def change_tracing(**kwargs):
    TRAME_VIEWER.change_tracing(kwargs["toggle_tracing"])


@state.change("toggle_profiling")
def change_profiling(**kwargs):
    TRAME_VIEWER.change_profiling(kwargs["toggle_profiling"])


@state.change("toggle_interpolation")
def change_interpolation(**kwargs):
    TRAME_VIEWER.change_interpolation(kwargs["toggle_interpolation"])


@state.change("show_slice_histogram")
def show_slice_histogram(**kwargs):
    TRAME_VIEWER.show_slice_histogram(kwargs["show_slice_histogram"])


if __name__ == "__main__":
    sys.exit(main())
