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
    build.base_layer = base_image
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
    finally:
        application.clean()


def test_caching(target_image, application, build):
    try:
        application.build(basic_playbook_path, build)
        b2 = Build.from_json(build.to_dict())
        application.build(basic_playbook_path, b2)
        build = application.db.get_build(build.build_id)
        b2 = application.db.get_build(b2.build_id)
        assert b2.progress == build.progress
        assert len(build.progress) == 4
    finally:
        application.clean()


def test_disabled_caching(target_image, application, build):
    build.cache_tasks = False
    try:
        application.build(basic_playbook_path, build)
        build = application.db.get_build(build.build_id)
        assert build.base_image == build.base_layer
        assert len(build.progress) == 0
    finally:
        application.clean()
