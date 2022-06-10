#!/usr/bin/env bash

git clone https://github.com/vais-ral/CILViewer

. /home/abc/mambaforge/etc/profile.d/conda.sh
conda activate cilviewer_webapp
pip install CILViewer/Wrappers/Python

rm -rf CILViewer