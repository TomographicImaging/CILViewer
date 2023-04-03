# GitHub Actions

## Building the Conda Package: [conda_build_and_publish](https://github.com/vais-ral/CILViewer/blob/master/.github/workflows/conda_build_and_publish.yml)
This github action builds and tests the conda package, by using the [conda-package-publish-action](https://github.com/paskino/conda-package-publish-action)

When making an [annotated](https://git-scm.com/book/en/v2/Git-Basics-Tagging) tag, the code is built, tested and published to the [ccpi conda channel for ccpi-viewer](https://anaconda.org/ccpi/ccpi-viewer/files) as noarch package, as pure python. Previously we provided packages for linux, windows and macOS versions.

When pushing to master, or opening or modifying a pull request to master, a single variant is built and tested, but not published. This variant is `python=3.7` and `numpy=1.18`. Notice that we removed the variants from the recipe as we do not have a strong dependency on numpy or python.
