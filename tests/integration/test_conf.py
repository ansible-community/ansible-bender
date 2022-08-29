import json
import os
from pathlib import Path

import jsonschema
import pytest

from ansible_bender.conf import ImageMetadata, Build
from ansible_bender.core import PbVarsParser
from ansible_bender.db import Database
from ansible_bender.exceptions import ABValidationError
from ansible_bender.utils import set_logging
from tests.spellbook import b_p_w_vars_path, basic_playbook_path, full_conf_pb_path, multiplay_path, \
    playbook_with_unknown_keys, playbook_wrong_type


def test_expand_pb_vars():
    p = PbVarsParser(b_p_w_vars_path)
    data = p.expand_pb_vars()
    assert data["base_image"] == "quay.io/biocontainers/python:3"
    assert data["verbose_layer_names"]
    playbook_dir = os.path.dirname(b_p_w_vars_path)
    assert data["working_container"]["volumes"] == [f"{playbook_dir}:/src:Z"]
    assert data["target_image"]["name"] == "challet"
    assert data["target_image"]["labels"] == {"x": "y"}
    assert data["target_image"]["environment"] == {"asd": playbook_dir}


def test_b_m_empty():
    """ test that build and metadata are 'empty' when there are no vars """
    p = PbVarsParser(basic_playbook_path)
    b, m = p.get_build_and_metadata()
    b.playbook_path = "/somewhere.yaml"

    b.base_image = "fedora:29"
    b.playbook_path = "/asd.yaml"
    b.target_image = "lolz"

    b.validate()
    m.validate()
    assert isinstance(b, Build)
    assert isinstance(m, ImageMetadata)
    assert b.cache_tasks is True
    assert b.layering is True


def test_set_all_params():
    """ test that we can set all the parameters """
    p = PbVarsParser(full_conf_pb_path)
    b, m = p.get_build_and_metadata()
    b.playbook_path = "/somewhere.yaml"

    b.validate()
    m.validate()

    assert isinstance(b, Build)
    assert isinstance(m, ImageMetadata)

    assert b.base_image == "mona_lisa"
    assert b.layering
    assert not b.cache_tasks
    assert b.ansible_extra_args == "--some --args"
    assert b.buildah_run_extra_args == "--hostname=foo"
    assert b.podman_run_extra_args == "--network=host -e=FOO=BAR"
    assert b.build_volumes == ["/c:/d"]
    assert b.build_entrypoint == "ls"
    assert b.target_image == "funky-mona-lisa"

    assert m.env_vars == {"z": "value"}
    assert m.volumes == ["/a"]
    assert m.working_dir == "/workshop"
    assert m.labels == {"x": "y"}
    assert m.annotations == {"bohemian": "rhapsody"}
    assert m.cmd == "command -x -y z"
    assert m.entrypoint == "great-entry-point"
    assert m.user == "leonardo"


def test_validation_err_ux():
    """ Test that validation errors are useful """
    p = PbVarsParser(basic_playbook_path)
    b, m = p.get_build_and_metadata()

    with pytest.raises(jsonschema.exceptions.ValidationError) as ex:
        b.validate()

    s = str(ex.value)

    assert "is not of type" in s
    assert "Failed validating 'type' in schema" in s


@pytest.mark.parametrize(
    "path,message",
    (
        (
            playbook_with_unknown_keys,
            "Additional properties are not allowed ('unknown_key' was unexpected)"
        ),
        (playbook_wrong_type, "variable /target_image is set to my-image-name, which is not of type object, null")
    )
)
def test_validation_err_ux2(path, message):
    """ Test that validation errors are useful """
    p = PbVarsParser(path)
    with pytest.raises(ABValidationError) as ex:
        p.get_build_and_metadata()
    s = str(ex.value)
    assert message in s


def test_multiplay(caplog):
    set_logging()
    p = PbVarsParser(multiplay_path)
    b, m = p.get_build_and_metadata()

    assert b.target_image != "nope"
    assert "Variables are loaded only from the first play." == caplog.records[0].msg
    assert "no bender data found in the playbook" == caplog.records[1].msg


def test_backwards_compat(tmpdir):
    """
    we keep adding new fields in DB: this test makes sure that none of them are required
    so that old config is forward compat with new versions of ab
    """
    db_dir_path = str(tmpdir)
    db = Database(db_path=db_dir_path)
    db_path = db._db_path()
    db_content = {
        "next_build_id": 2,
        "builds": {
            "1": {
                "build_id": "1",
                "playbook_path": "playbook.yaml",
                "build_volumes": [],
                "build_user": None,
                "metadata": {
                    "working_dir": "/src",
                    "labels": {},
                    "annotations": {},
                    "env_vars": {},
                    "cmd": None,
                    "user": None,
                    "ports": [],
                    "volumes": []
                },
                "state": "done",
                "build_start_time": "20190923-153518169396",
                "build_finished_time": "20190923-153531854630",
                "base_image": "fedora:30",
                "target_image": "ansiblefest-image",
                "builder_name": "buildah",
                "layers": [
                    {
                        "content": None,
                        "layer_id": "e9ed59d2baf72308f3a811ebc49ff3f4e0175abf40bf636bea0160759c637999",
                        "base_image_id": None,
                        "cached": True
                    },
                    {
                        "content": "730ecc32518d080377233c10f42ec832f3834cc933ff42a32cbb",
                        "layer_id": "6e96477fc1760c4b325af2411b0b3eeb7329ad498e1f12d3f45407b468370c87",
                        "base_image_id": "e9ed59d2baf72308f3a811ebc49ff3f4e0175abf40bf636bea0160759c637999",
                        "cached": False
                    },
                    {
                        "content": "ffdc7f85f0fe7a9b72fe172d2e54c7d39daf81d7779dcf560d729",
                        "layer_id": "ccaa5ef34c2d6afacf8017f00d0ae3ce325ac9e282a49acedcbb166c8a3e23b9",
                        "base_image_id": "6e96477fc1760c4b325af2411b0b3eeb7329ad498e1f12d3f45407b468370c87",
                        "cached": False
                    }
                ],
                "final_layer_id": "55187e2caf8e5f0c8b5e6c863779701328dc9de17a3cd07525894a6e2e41339f",
                "layer_index": {
                    "e9ed59d2baf72308f3a811ebc49ff3f4e0175abf40bf636bea0160759c637999": {
                        "content": None,
                        "layer_id": "e9ed59d2baf72308f3a811ebc49ff3f4e0175abf40bf636bea0160759c637999",
                        "base_image_id": None,
                        "cached": True
                    },
                    "6e96477fc1760c4b325af2411b0b3eeb7329ad498e1f12d3f45407b468370c87": {
                        "content": "730ecc32518d080377233c10f42ec832f3834cc933ff42a32cbb54bb4",
                        "layer_id": "6e96477fc1760c4b325af2411b0b3eeb7329ad498e1f12d3f45407b468370c87",
                        "base_image_id": "e9ed59d2baf72308f3a811ebc49ff3f4e0175abf40bf636bea0160759c637999",
                        "cached": False
                    },
                    "ccaa5ef34c2d6afacf8017f00d0ae3ce325ac9e282a49acedcbb166c8a3e23b9": {
                        "content": "ffdc7f85f0fe7a9b72fe172d2e54c7d39daf81d7779dcf560d729e99",
                        "layer_id": "ccaa5ef34c2d6afacf8017f00d0ae3ce325ac9e282a49acedcbb166c8a3e23b9",
                        "base_image_id": "6e96477fc1760c4b325af2411b0b3eeb7329ad498e1f12d3f45407b468370c87",
                        "cached": False
                    }
                },
                "build_container": "ansiblefest-image-20190923-153517420660-cont",
                "cache_tasks": True,
                "log_lines": [""],
                "layering": True,
                "debug": True,
                "verbose": True,
                "pulled": True,
                "buildah_from_extra_args": None,
                "ansible_extra_args": "",
                "python_interpreter": "",
                "verbose_layer_names": ""
            },

        }
    }
    Path(db_path).write_text(json.dumps(db_content))
    assert db.load_builds()
