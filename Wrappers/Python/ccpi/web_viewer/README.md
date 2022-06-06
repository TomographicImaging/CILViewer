To setup your environment for using the web application we recommend using conda as it can simplify things in comparison to other implementations of python environment handling.

Follow these steps:
- Install a variant of conda for this example we will use mambaforge (includes mamba (faster conda implementation) and has conda-forge added as a default channel), it can be downloaded here: https://github.com/conda-forge/miniforge/releases
- Create the conda environment:
    - `mamba env create -f dev-environment.yml`
- With the activated conda environment you can now start the web application:
    - `python web_app.py path/to/folder/of/data/to/use`
- If you want to use the 2D viewer pass the 2D arg to the script i.e. --2D or -d:
    - `python web_app.py --2D path/to/folder/of/data/to/use`