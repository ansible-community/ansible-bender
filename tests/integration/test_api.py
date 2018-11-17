"""
Test Application class
"""
import os
import shutil

from ansible_bender.api import Application
from ansible_bender.builders.base import Build, ImageMetadata, BuildState
from tests.spellbook import dont_cache_playbook_path, change_layering_playbook, data_dir, dont_cache_playbook_path_pre
from ..spellbook import basic_playbook_path, small_basic_playbook_path, base_image, target_image

import pytest
import yaml


@pytest.fixture()
def application(tmpdir):
    database_path = str(tmpdir)
    application = Application(db_path=database_path)  # use debug=True to hunt errors
    yield application
    application.clean()


@pytest.fixture()
def build(target_image):
    build = Build()
    build.playbook_path = basic_playbook_path
    build.base_image = base_image
    build.target_image = target_image
    build.metadata = ImageMetadata()
    build.state = BuildState.NEW
    build.builder_name = "buildah"  # test with all builders
    return build


def test_build_db_metadata(target_image, application, build):
    application.build(build)
    build = application.db.get_build(build.build_id)
    assert build.playbook_path is not None
    assert build.build_finished_time is not None
    assert build.build_start_time is not None
    assert build.log_lines is not None
    logs = "\n".join(build.log_lines)
    assert "PLAY [all]" in logs
    assert "TASK [Gathering Facts]" in logs
    assert "failed=0" in logs


def test_caching(target_image, application, build):
    b2 = Build.from_json(build.to_dict())
    application.build(build)
    b2.build_id = None
    b2.layers = []
    b2.target_image += "2"
    application.build(b2)
    build = application.db.get_build(build.build_id)
    b2 = application.db.get_build(b2.build_id)
    assert [x.layer_id for x in b2.layers[:3]] == [y.layer_id for y in build.layers[:3]]
    assert not b2.layers[4].cached
    assert not build.layers[4].cached
    assert len(build.layers) == 5


def test_disabled_caching(target_image, application, build):
    build.cache_tasks = False
    application.build(build)
    build = application.db.get_build(build.build_id)
    assert len(build.layers) == 5
    assert build.layers[0].cached
    assert not build.layers[1].cached
    assert not build.layers[2].cached
    assert not build.layers[3].cached
    assert not build.layers[4].cached


def test_caching_mechanism(target_image, application, build):
    """ check that previously executed tasks are being loaded from cache and new ones are computed from scratch """
    small_build = Build.from_json(build.to_dict())
    small_build.target_image += "2"
    small_build.playbook_path = small_basic_playbook_path

    application.build(small_build)
    small_build = application.db.get_build(small_build.build_id)
    assert len(small_build.layers) == 2
    assert small_build.layers[0].cached
    assert not small_build.layers[1].cached

    application.build(build)
    build = application.db.get_build(build.build_id)
    assert len(build.layers) == 5
    assert build.layers[0].cached
    assert build.layers[1].cached
    assert not build.layers[2].cached
    assert not build.layers[3].cached
    assert not build.layers[4].cached


def test_no_cache_tag(target_image, application, build):
    """ utilize a playbook which halts caching """
    dont_cache_b = Build.from_json(build.to_dict())
    build.playbook_path = dont_cache_playbook_path_pre

    application.build(build)
    build = application.db.get_build(build.build_id)
    assert len(build.layers) == 4
    assert build.layers[0].cached
    assert not build.layers[1].cached
    assert not build.layers[2].cached
    assert not build.layers[3].cached

    dont_cache_b.target_image += "2"
    dont_cache_b.playbook_path = dont_cache_playbook_path

    application.build(dont_cache_b)
    dont_cache_b = application.db.get_build(dont_cache_b.build_id)
    assert len(dont_cache_b.layers) == 4
    assert dont_cache_b.layers[0].cached
    assert dont_cache_b.layers[1].cached
    assert not dont_cache_b.layers[2].cached
    assert not dont_cache_b.layers[3].cached

    builder = application.get_builder(dont_cache_b)
    builder.run(dont_cache_b.target_image, ["ls", "-1", "/asd"])


def test_stop_layering(target_image, application, build):
    """ utilize a playbook which halts caching """
    build.playbook_path = change_layering_playbook
    application.build(build)
    build = application.db.get_build(build.build_id)
    assert len(build.layers) == 3  # base image, first task and the final layer

    builder = application.get_builder(build)
    builder.run(build.target_image, ["ls", "-1", "/etc/passwd-lol"])


def test_file_caching_mechanism(tmpdir, target_image, application, build):
    """ make sure that we don't load from cache when a file was changed """
    t = str(tmpdir)
    pb_name = "file_caching.yaml"
    test_file_name = "a_bag_of_fun"
    file_caching_pb = os.path.join(data_dir, pb_name)
    p = os.path.join(t, pb_name)
    test_file = os.path.join(data_dir, test_file_name)
    f = os.path.join(t, test_file_name)

    shutil.copy(file_caching_pb, p)
    shutil.copy(test_file, f)

    with open(p) as fd:
        d = yaml.safe_load(fd)
        d[0]["tasks"][0]["copy"]["src"] = f
    with open(p, "w") as fd:
        yaml.safe_dump(d, fd)

    build.playbook_path = p
    second_build = Build.from_json(build.to_dict())
    cached_build = Build.from_json(build.to_dict())

    application.build(build)
    build = application.db.get_build(build.build_id)
    assert len(build.layers) == 2
    assert build.layers[0].cached
    assert not build.layers[1].cached

    # ideally this would be cached, but isn't now
    application.build(cached_build)
    cached_build = application.db.get_build(cached_build.build_id)
    assert len(cached_build.layers) == 2
    assert cached_build.layers[0].cached
    # since ansible doesn't track files and whether they changed, let's just make sure it works we expect it to work
    assert not cached_build.layers[1].cached

    # and now we test that if we change the file, it's not loaded from cache
    fun_content = "Much more fun, fun, fun!"
    with open(f, "w") as fd:
        fd.write(fun_content)

    application.build(second_build)
    second_build = application.db.get_build(second_build.build_id)
    assert not second_build.layers[1].cached

    builder = application.get_builder(second_build)
    out = builder.run(second_build.target_image, ["cat", "/fun"])
    assert out == fun_content
