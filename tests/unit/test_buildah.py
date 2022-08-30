import json

from ansible_bender.builders import buildah_builder
from ansible_bender.builders.buildah_builder import BuildahBuilder, get_buildah_image_id
from ansible_bender.conf import Build
from flexmock import flexmock

from tests.spellbook import base_image, buildah_inspect_data_path


def mock_inspect():
    with open(buildah_inspect_data_path) as fd:
        buildah_inspect_data = json.load(fd)
    flexmock(buildah_builder, inspect_resource=lambda x, y: buildah_inspect_data)


def test_buildah_id():
    mock_inspect()
    assert get_buildah_image_id("this-is-mocked") == "6aed6d59a707a7040ad25063eafd3a2165961a2c9f4d1d06ed0a73bdf2a89322"

def test_extra():
    build = Build()
    build.base_image = base_image
    build.podman_run_extra_args = "--network=host -e=FOO=BAR"
    build.buildah_run_extra_args = "--hostname=foo"
    b = BuildahBuilder(build, debug=True)
    assert b.podman_run_args == ["--network=host", "-e=FOO=BAR"]
    assert b.buildah_run_args == ["--hostname=foo"]
