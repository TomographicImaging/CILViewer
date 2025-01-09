#!/usr/bin/env bash

# https://stackoverflow.com/a/246128
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]:-$0}"; )" &> /dev/null && pwd 2> /dev/null; )";
INSTALL_DIR=$HOME/mambaforge

cd $HOME
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash $HOME/Miniforge3-$(uname)-$(uname -m).sh -b -p $INSTALL_DIR
rm $HOME/Miniforge3-Linux-x86_64.sh
. $INSTALL_DIR/etc/profile.d/conda.sh
mamba env create -f $SCRIPT_DIR/environment.yml
conda activate cilviewer_webapp
