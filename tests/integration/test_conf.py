import os

import jsonschema
import pytest
from ansible_bender.utils import set_logging

from ansible_bender.conf import ImageMetadata, Build
from ansible_bender.core import PbVarsParser

from tests.spellbook import b_p_w_vars_path, basic_playbook_path, full_conf_pb_path, multiplay_path


def test_expand_pb_vars():
    p = PbVarsParser(b_p_w_vars_path)
    data = p.expand_pb_vars()
    assert data["base_image"] == "docker.io/library/python:3-alpine"
    assert data["ansible_extra_args"] == "-vvv"
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
    assert b.build_volumes == ["/c:/d"]
    assert b.target_image == "funky-mona-lisa"

    assert m.env_vars == {"z": "value"}
    assert m.volumes == ["/a"]
    assert m.working_dir == "/workshop"
    assert m.labels == {"x": "y"}
    assert m.annotations == {"bohemian": "rhapsody"}
    assert m.cmd == "command -x -y z"
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


def test_multiplay(caplog):
    set_logging()
    p = PbVarsParser(multiplay_path)
    b, m = p.get_build_and_metadata()

    assert b.target_image != "nope"
    assert "Variables are loaded only from the first play." == caplog.records[0].msg
    assert "no bender data found in the playbook" == caplog.records[1].msg
