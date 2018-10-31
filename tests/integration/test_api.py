"""
Test Application class
"""
from ansible_bender.api import Application
from ansible_bender.builders.base import Build, ImageMetadata, BuildState
from ..spellbook import basic_playbook_path, base_image, target_image

import pytest


@pytest.fixture()
def application(tmpdir):
    database_path = str(tmpdir)
    return Application(db_path=database_path)


@pytest.fixture()
def build(target_image):
    build = Build()
    build.base_image = base_image
    build.target_image = target_image
    build.metadata = ImageMetadata()
    build.state = BuildState.NEW
    build.builder_name = "buildah"  # test with all builders
    return build


def test_build_db_metadata(target_image, application, build):
    try:
        application.build(basic_playbook_path, build)
        build = application.db.get_build(build.build_id)
        assert build.build_finished_time is not None
        assert build.build_start_time is not None
        assert build.log_lines is not None
        logs = "\n".join(build.log_lines)
        assert "PLAY [all]" in logs
        assert "TASK [Gathering Facts]" in logs
        assert "failed=0" in logs
    finally:
        application.clean()


def test_caching(target_image, application, build):
    try:
        b2 = Build.from_json(build.to_dict())
        application.build(basic_playbook_path, build)
        b2.build_id = None
        b2.layers = []
        b2.target_image += "2"
        application.build(basic_playbook_path, b2)
        build = application.db.get_build(build.build_id)
        b2 = application.db.get_build(b2.build_id)
        assert [x.layer_id for x in b2.layers] == [y.layer_id for y in build.layers]
        assert len(build.layers) == 5
    finally:
        application.clean()


def test_disabled_caching(target_image, application, build):
    build.cache_tasks = False
    try:
        application.build(basic_playbook_path, build)
        build = application.db.get_build(build.build_id)
        base_image_id = application.get_builder(build).get_image_id(build.base_image)
        assert base_image_id == build.get_top_layer_id()
        assert len([x for x in build.layers if x.cached]) == 1
    finally:
        application.clean()
