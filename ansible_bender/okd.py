""" Build inside OKD as a custom build """
import json
import os
import shutil
import tempfile

from ansible_bender.builders.base import BuildState
from ansible_bender.conf import ImageMetadata, Build
from ansible_bender.utils import env_get_or_fail_with, graceful_get, git_clone_to_path


def okd_load_metadata():
    """ load metadata about the build from the BUILD env var """
    b = env_get_or_fail_with("BUILD", "BUILD environment variable is not set, are you running in openshift?")
    bd = json.loads(b)
    response = (
        graceful_get(bd, "spec", "source", "git", "uri"),
        graceful_get(bd, "spec", "source", "git", "ref"),
        graceful_get(bd, "spec", "output", "to", "name"),
    )
    if not all(response):
        raise RuntimeError("Not all build parameters seem to be set, halting.")
    return response


def okd_get_playbook_base():
    """ load metadata from os.environ and return playbook path & base image name """
    return (env_get_or_fail_with("AB_PLAYBOOK_PATH", "Can't get playbook path from the environment"),
            env_get_or_fail_with("AB_BASE_IMAGE", "Can't get base image name from the environment"))


def build_inside_openshift(app):
    """
    This is expected to run inside an openshift pod spawned via custom build

    :param app: instance of Application
    """
    playbook_path, base_image = okd_get_playbook_base()

    if playbook_path.startswith("/"):
        raise RuntimeError("The path to playbook needs to be relative within the git repo.")

    uri, ref, target_image = okd_load_metadata()

    tmp = tempfile.mkdtemp(prefix="ab-okd")

    try:
        git_clone_to_path(uri, tmp, ref=ref)

        playbook_path = os.path.abspath(os.path.join(tmp, playbook_path))
        if not playbook_path.startswith(tmp):
            raise RuntimeError("The path to playbook points outside of the git repo, this is not allowed.")

        build = Build()
        build.metadata = ImageMetadata()  # TODO: needs to be figured out
        build.playbook_path = playbook_path
        build.base_image = base_image
        build.target_image = target_image
        build.builder_name = "buildah"
        build.cache_tasks = False  # we have local storage in pod, so this doesn't make any sense
        app.build(build)

    finally:
        shutil.rmtree(tmp)
    # TODO: push
