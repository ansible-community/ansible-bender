import subprocess

from ansible_bender.api import Application
from ansible_bender.builders.base import Build, ImageMetadata, BuildState
from ansible_bender.builders.buildah_builder import buildah

from .spellbook import random_word, basic_playbook_path, base_image

import pytest


@pytest.fixture()
def target_image():
    im = "registry.example.com/ab-test-" + random_word(12) + ":oldest"
    yield im
    try:
        buildah("rmi", [im])  # FIXME: use builder interface instead for sake of other backends
        # FIXME: also remove everything from cache
    except subprocess.CalledProcessError as ex:
        print(ex)


@pytest.fixture()
def application(tmpdir):
    database_path = str(tmpdir)
    application = Application(db_path=database_path)  # use debug=True to hunt errors
    yield application
    application.clean()


@pytest.fixture()
def build(target_image):
    build = Build()
    build.playbook_path = basic_playbook_path
    build.base_image = base_image
    build.target_image = target_image
    build.metadata = ImageMetadata()
    build.state = BuildState.NEW
    build.builder_name = "buildah"  # test with all builders
    return build
