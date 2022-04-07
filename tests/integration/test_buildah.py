import logging
import subprocess
from subprocess import CalledProcessError

import pytest
from flexmock import flexmock

from ansible_bender.builders import buildah_builder
from ansible_bender.builders.buildah_builder import BuildahBuilder, buildah_run_cmd
from ansible_bender.conf import Build
from ansible_bender.utils import set_logging
from tests.spellbook import base_image

BUILDAH_15_VERSION = """ \
Version:         1.5
Go Version:      go1.11.5
Image Spec:      1.0.0
Runtime Spec:    1.0.0
CNI Spec:        0.4.0
libcni Version:
Git Commit:
Built:           Thu Jan  1 00:00:00 1970
OS/Arch:         linux/amd64
"""


@pytest.mark.parametrize("image_name,found", [
    ("registry.fedoraproject.org/fedora:33", True),
    ("registry.access.redhat.com/ubi8/python-38", True),
    (base_image, True),
    ("quay.io/quay/busybox", False),
    ])
def test_find_py_intrprtr_in_fedora_image(image_name, found):
    build = Build()
    build.base_image = image_name
    build.target_image = "starena"
    bb = BuildahBuilder(build)
    try:
        assert bb.find_python_interpreter()
    except RuntimeError:
        if found:
            # interpreter should have been found
            raise


def test_get_version():
    b = BuildahBuilder(Build(), debug=True)
    version = b.get_buildah_version()
    assert [x for x in version if isinstance(x, int)]


def test_get_version_rhel_8():
    flexmock(buildah_builder, run_cmd=lambda *args, **kwargs: BUILDAH_15_VERSION)
    b = BuildahBuilder(Build(), debug=True)
    version = b.get_buildah_version()
    assert [x for x in version if isinstance(x, int)]
    assert version < (1, 7, 3)


@pytest.mark.parametrize("command,err_message,exit_code", [
    # sometimes it's "No", sometimes it's "no"
    (["/I-dont-exist"], "o such file or directory", None),
    # the message is inconsistent, let's use the return code instead
    (["false"], None, 1),
])
def test_buildah_run_cmd(command, err_message, exit_code):
    try:
        buildah_run_cmd(base_image, "autumn", command)
    except subprocess.CalledProcessError as e:
        if err_message is not None:
            assert err_message in e.stderr
        elif exit_code is not None:
            assert exit_code == e.returncode


def test_buildah_sanity_check_extra_args(caplog):
    set_logging(level=logging.DEBUG)
    build = Build()
    build.base_image = base_image
    build.buildah_from_extra_args = "--help"
    b = BuildahBuilder(build, debug=True)
    b.ansible_host = "cacao"
    with pytest.raises(CalledProcessError):
        b.sanity_check()
    for r in caplog.records:
        if "-h, --help" in r.message:
            break
    else:
        assert 1/0, "it seems that buildah_from_extra_args were not passed to sanity check"

