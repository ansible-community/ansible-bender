import pytest

from ansible_bender.builders.buildah_builder import BuildahBuilder


@pytest.mark.parametrize("image_name,found", [
    ("registry.fedoraproject.org/fedora:28", True),
    ("docker.io/library/python:3-alpine", True),
    ("docker.io/library/busybox", False),
    ])
def test_find_py_intrprtr_in_fedora_image(image_name, found):
    bb = BuildahBuilder(image_name, "asdqwe", None)
    try:
        assert bb.find_python_interpreter()
    except RuntimeError:
        if found:
            # interpreter should have been found
            raise
