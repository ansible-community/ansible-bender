import logging
import subprocess

import pytest

from ansible_bender.api import Application
from ansible_bender.builders.base import BuildState
from ansible_bender.builders.buildah_builder import buildah
from ansible_bender.conf import ImageMetadata, Build
from ansible_bender.utils import set_logging
from .spellbook import random_word, basic_playbook_path, base_image, project_dir


logger = set_logging(level=logging.DEBUG)


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
    build.debug = True
    build.playbook_path = basic_playbook_path
    build.base_image = base_image
    build.target_image = target_image
    build.metadata = ImageMetadata()
    build.state = BuildState.NEW
    build.builder_name = "buildah"  # test with all builders
    return build


def ab(args, tmpdir_path, return_output=False, ignore_result=False, env=None):
    """
    python3 -m ab.cli -v build ./playbook.yaml registry.fedoraproject.org/fedora:28 asdqwe-image

    :return:
    """
    # put --debug in there for debugging
    cmd = ["python3", "-m", "ansible_bender.cli", "--database-dir", tmpdir_path] + args
    logger.debug("cmd = %s", cmd)
    if ignore_result:
        return subprocess.call(cmd, cwd=project_dir, env=env)
    if return_output:
        return subprocess.check_output(
            cmd, cwd=project_dir, universal_newlines=True, stderr=subprocess.STDOUT, env=env)
    else:
        # don't use run_cmd here, it makes things complicated
        subprocess.check_call(cmd, cwd=project_dir, env=env)
