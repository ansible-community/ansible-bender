import pytest

from ansible_bender.builders.buildah_builder import BuildahBuilder
from ansible_bender.conf import Build


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
