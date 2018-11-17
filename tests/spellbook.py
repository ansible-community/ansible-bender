import logging
import os
import random
import string
import subprocess

import pytest

from ansible_bender.builders.buildah_builder import buildah
from ansible_bender.utils import set_logging


set_logging(level=logging.DEBUG)


tests_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(tests_dir)
data_dir = os.path.join(tests_dir, "data")
basic_playbook_path = os.path.join(data_dir, "basic_playbook.yaml")
basic_playbook_path_w_bv = os.path.join(data_dir, "basic_playbook_with_volume.yaml")
dont_cache_playbook_path_pre = os.path.join(data_dir, "dont_cache_playbook_pre.yaml")
dont_cache_playbook_path = os.path.join(data_dir, "dont_cache_playbook.yaml")
small_basic_playbook_path = os.path.join(data_dir, "small_basic_playbook.yaml")
change_layering_playbook = os.path.join(data_dir, "change_layering.yaml")
bad_playbook_path = os.path.join(data_dir, "bad_playbook.yaml")
base_image = "docker.io/library/python:3-alpine"


@pytest.fixture()
def target_image():
    im = "registry.example.com/ab-test-" + random_word(12) + ":oldest"
    yield im
    try:
        buildah("rmi", [im])  # FIXME: use builder interface instead for sake of other backends
        # FIXME: also remove everything from cache
    except subprocess.CalledProcessError as ex:
        print(ex)


def random_word(length):
    # https://stackoverflow.com/a/2030081/909579
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))
