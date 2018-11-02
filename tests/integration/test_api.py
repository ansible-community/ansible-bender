"""
Test Application class
"""
from ansible_bender.api import Application
from ansible_bender.builders.base import Build, ImageMetadata, BuildState
from tests.spellbook import dont_cache_playbook_path, change_layering_playbook
from ..spellbook import basic_playbook_path, small_basic_playbook_path, base_image, target_image

import pytest


@pytest.fixture()
def application(tmpdir):
    database_path = str(tmpdir)
    application = Application(db_path=database_path)  # use debug=True to hunt errors
    yield application
    application.clean()


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
    application.build(basic_playbook_path, build)
    build = application.db.get_build(build.build_id)
    assert build.build_finished_time is not None
    assert build.build_start_time is not None
    assert build.log_lines is not None
    logs = "\n".join(build.log_lines)
    assert "PLAY [all]" in logs
    assert "TASK [Gathering Facts]" in logs
    assert "failed=0" in logs


def test_caching(target_image, application, build):
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


def test_disabled_caching(target_image, application, build):
    build.cache_tasks = False
    application.build(basic_playbook_path, build)
    build = application.db.get_build(build.build_id)
    base_image_id = application.get_builder(build).get_image_id(build.base_image)
    assert base_image_id == build.get_top_layer_id()
    assert len([x for x in build.layers if x.cached]) == 1


def test_caching_mechanism(target_image, application, build):
    """ check that previously executed tasks are being loaded from cache and new ones are computed from scratch """
    small_build = Build.from_json(build.to_dict())
    small_build.target_image += "2"

    application.build(small_basic_playbook_path, small_build)
    small_build = application.db.get_build(small_build.build_id)
    assert len(small_build.layers) == 2
    assert small_build.layers[0].cached
    assert not small_build.layers[1].cached

    application.build(basic_playbook_path, build)
    build = application.db.get_build(build.build_id)
    assert len(build.layers) == 5
    assert build.layers[0].cached
    assert build.layers[1].cached
    assert not build.layers[2].cached
    assert not build.layers[3].cached
    assert not build.layers[4].cached


def test_dont_cache_tag(target_image, application, build):
    """ utilize a playbook which halts caching """
    dont_cache_b = Build.from_json(build.to_dict())

    application.build(basic_playbook_path, build)
    build = application.db.get_build(build.build_id)
    assert len(build.layers) == 5
    assert build.layers[0].cached
    assert not build.layers[1].cached
    assert not build.layers[2].cached

    dont_cache_b.target_image += "2"

    application.build(dont_cache_playbook_path, dont_cache_b)
    dont_cache_b = application.db.get_build(dont_cache_b.build_id)
    assert len(dont_cache_b.layers) == 5
    assert dont_cache_b.layers[0].cached
    assert dont_cache_b.layers[1].cached
    assert not dont_cache_b.layers[2].cached
    assert not dont_cache_b.layers[3].cached
    assert not dont_cache_b.layers[4].cached


def test_stop_layering(target_image, application, build):
    """ utilize a playbook which halts caching """
    application.build(change_layering_playbook, build)
    build = application.db.get_build(build.build_id)
    assert len(build.layers) == 2  # base image, first task (the final layer is not present here)

    builder = application.get_builder(build)
    builder.run(build.target_image, ["ls", "-1", "/etc/passwd-lol"])


def test_file_caching_mechanism(target_image, application, build):
    # TODO: skip caching for files: when a task wasn't changed
    #       likely skip tasks which are related to file operations
    #       in task result, if it's not changed, load from cache and continue the cache chain
    return True
