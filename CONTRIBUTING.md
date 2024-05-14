# Developer Contribution Guide
Contribute to the repository by opening a pull request.

## Local
Develop code locally by cloning the source code and installing it.

```sh
# Clone (download) source code
git clone git@github.com:TomographicImaging/CILViewer.git
cd CILViewer
# Install
pip install ./Wrappers/Python
```

### Run tests
Before merging a pull request, all tests must pass. 
Install the required packages:
```sh
pip install pytest
pip install pillow
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
