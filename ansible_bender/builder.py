"""
Builder interface
"""
import logging

from ansible_bender.builders.buildah_builder import BuildahBuilder


logger = logging.getLogger(__name__)


BUILDERS = {
    BuildahBuilder.name: BuildahBuilder
}


def get_builder(builder_name):
    try:
        return BUILDERS[builder_name]
    except KeyError:
        raise RuntimeError("No such builder %s", builder_name)
