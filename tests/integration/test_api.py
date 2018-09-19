"""
Test Application class
"""
from ansible_bender.api import Application
from ansible_bender.builders.base import Build, ImageMetadata, BuildState
from ..spellbook import basic_playbook_path, base_image, target_image


def test_caching(target_image):
    build = Build()
    build.base_image = base_image
    build.base_layer = base_image
    build.target_image = target_image
    build.metadata = ImageMetadata()
    build.state = BuildState.NEW
    build.builder_name = "buildah"  # test with all builders
    a = Application()
    try:
        a.build(basic_playbook_path, build)
        b2 = Build.from_json(build.to_dict())
        a.build(basic_playbook_path, b2)
        build = a.db.get_build(build.build_id)
        b2 = a.db.get_build(b2.build_id)
        assert b2.progress == build.progress
        assert len(build.progress) == 4
    finally:
        a.clean()


def test_disabled_caching(target_image):
    build = Build()
    build.base_image = base_image
    build.base_layer = base_image
    build.target_image = target_image
    build.metadata = ImageMetadata()
    build.state = BuildState.NEW
    build.builder_name = "buildah"  # test with all builders
    build.cache_tasks = False
    a = Application()
    try:
        a.build(basic_playbook_path, build)
        build = a.db.get_build(build.build_id)
        assert build.base_image == build.base_layer
        assert len(build.progress) == 0
    finally:
        a.clean()
