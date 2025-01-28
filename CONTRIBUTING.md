# Developer Contribution Guide
Contribute to the repository by opening a pull request.

## Local
Clone the source code.
```sh
git clone git@github.com:TomographicImaging/CILViewer.git
```
Navigate the folder.
```sh
cd CILViewer
```

Create a new environment. 
```sh
conda env create –f Wrappers/Python/conda-recipe/environment.yml
```
Activate the environment.
```sh
conda activate cilviewer
```
Install the package.
```sh
pip install ./Wrappers/Python --no-dependencies
```

### Run tests
Before merging a pull request, all tests must pass. 
Install the required packages:
```sh
conda install eqt pillow pyside2 pytest -c ccpi cil-data=22.0.0
```
Tests can be run locally from the repository folder
```sh
python -m pytest Wrappers/Python/test
```

## Continuous integration

### Changelog
Located in [CHANGELOG.md](./CHANGELOG.md).

##### Changelog style
The changelog file needs to be updated manually every time a pull request (PR) is submitted.
- Itemise the message with "-".
- Be concise by explaining the overall changes in only a few words.
- Mention the relevant PR.

###### Example:
- Add CONTRIBUTING.md #403
