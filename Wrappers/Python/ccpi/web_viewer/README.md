To setup your environment for using the web application we recommend using conda as it can simplify things in comparison to other implementations of python environment handling.

Follow these steps:
- Install a variant of conda. For this example we will use mambaforge (includes mamba, a faster conda implementation, and has conda-forge added as a default channel). It can be downloaded here: https://github.com/conda-forge/miniforge/releases
- Create the conda environment:
    - `mamba env create -f dev-environment.yml`
- Activate the environment
    - `conda activate cilviewer_webapp` or `mamba activate cilviewer_webapp`
- Install the app in the environment from the `CILViewer` directory
    - `pip install ./Wrappers/Python`
- Start the web application
    - `web_cilviewer path/to/folder/of/data/to/use`
    where `path/to/folder/of/data/to/use` is the folder storing the data i.e. no filename included
- Pass the 2D arg to the script if you want to use the 2D viewer i.e. `--2D` or `-d args`. This needs to be added before the path
    - `web_cilviewer --2D path/to/folder/of/data/to/use`
