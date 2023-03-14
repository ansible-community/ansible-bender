"""
ab (ansible builder) is a tool which enables you to build container images using ansible

## Usage

$ ab build ./playbook.yaml fedora:28 my-custom-image

"""
try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from importlib_metadata import version, PackageNotFoundError

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed
    __version__ = None
