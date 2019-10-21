import pytest
from flexmock import flexmock

from ansible_bender.builders import buildah_builder
from ansible_bender.builders.buildah_builder import BuildahBuilder
from ansible_bender.conf import Build


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
    ("registry.fedoraproject.org/fedora:29", True),
    ("docker.io/library/python:3-alpine", True),
    ("docker.io/library/busybox", False),
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
