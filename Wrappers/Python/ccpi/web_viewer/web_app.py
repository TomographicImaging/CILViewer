#
#   Author 2022 Samuel Jones
#   Copyright 2022 SCD Rutherford Appleton Laboratory UKRI
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
import os
import sys

from ccpi.web_viewer.trame_viewer import TrameViewer


def data_finder(directory: str):
    """
    Finds all files that are needed to be passed to the TrameViewer that in a list that is digestible, given a directory
    :param directory: str, A file path to a directory containing data for use with the TrameViewer class.
    :return: list, of full file paths of data in the given directory parameter
    """
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"This path: '{directory}' is not to a file.")
    return os.listdir(directory)


def main() -> int:
    """
    Create the main class and run the TrameViewer
    :return: int, exit code for the program
    """
    try:
        input_directory = ""
        data_files = data_finder(input_directory)
        trame_viewer = TrameViewer(data_files)
    except Exception as e:
        print(str(e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
