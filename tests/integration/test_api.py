"""
Test Application class
"""
import os
import random
import string

import pytest

from ansible_bender.api import Application
from ansible_bender.builders.base import Build, ImageMetadata, BuildState
from ansible_bender.builders.buildah_builder import buildah

this_dir = os.path.dirname(os.path.abspath(__file__))
tests_dir = os.path.dirname(this_dir)
project_dir = os.path.dirname(tests_dir)
data_dir = os.path.join(tests_dir, "data")
basic_playbook_path = os.path.join(data_dir, "basic_playbook.yaml")
bad_playbook_path = os.path.join(data_dir, "bad_playbook.yaml")
base_image = "docker.io/library/python:3-alpine"


@pytest.fixture()
def target_image():
    im = "registry.example.com/ab-test-" + random_word(12) + ":oldest"
    yield im
    buildah("rmi", [im])  # FIXME: use builder interface instead


def random_word(length):
    # https://stackoverflow.com/a/2030081/909579
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


def test_caching(target_image):
    build = Build()
    build.base_image = base_image
    build.base_layer = base_image
    build.target_image = target_image
    build.metadata = ImageMetadata()
    build.state = BuildState.NEW
    build.builder_name = "buildah"  # test with all builders
    a = Application()
    try:
        a.build(basic_playbook_path, build)
        b2 = Build.from_json(build.to_dict())
        a.build(basic_playbook_path, b2)
        assert b2.progress == build.progress
    finally:
        a.clean()
