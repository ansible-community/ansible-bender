"""
ab (ansible builder) is a tool which enables you to build container images using ansible

## Usage

$ ab build ./playbook.yaml fedora:28 my-custom-image

"""
from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass
