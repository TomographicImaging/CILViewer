import sys
if sys.version_info.major >= 3 and sys.version_info.minor > 7:
    from importlib.metadata import version
else:
    from importlib_metadata import version

try:
    version = version("ccpi-viewer")
except:
    # package is not installed
    version = 'something bad happened'
