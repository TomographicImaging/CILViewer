#!/usr/bin/env bash

git clone https://github.com/vais-ral/CILViewer

. /home/abc/mambaforge/etc/profile.d/conda.sh
conda activate cilviewer_webapp
cd CILViewer/Wrappers/Python
pip install .

cd ../../..
rm -rf CILViewer