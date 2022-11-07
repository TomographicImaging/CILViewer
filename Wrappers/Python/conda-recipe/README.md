### Setting up a Development Environment
Clone https://github.com/vais-ral/CILViewer  

Install miniconda: https://docs.conda.io/en/latest/miniconda.html   

Navigate to the conda-recipe folder https://github.com/vais-ral/CILViewer/tree/master/Wrappers/Python/conda-recipe  

conda create –f environment.yml 

The above creates a new environment with everything you need installed. 

conda activate cilviewer_dev 

Navigate to the Wrappers/Python folder https://github.com/vais-ral/CILViewer/tree/master/Wrappers/Python  

pip install . --no-dependencies

