import os

from ansible_bender.builders.base import Build, ImageMetadata
from ansible_bender.core import PbVarsParser

from tests.spellbook import b_p_w_vars_path, basic_playbook_path, full_conf_pb_path


def test_expand_pb_vars():
    p = PbVarsParser(b_p_w_vars_path)
    data = p.expand_pb_vars()
    assert data["ansible_bender"]["base_image"] == "docker.io/library/python:3-alpine"
    assert data["ansible_bender"]["ansible_extra_args"] == "-vvv"
    playbook_dir = os.path.dirname(b_p_w_vars_path)
    assert data["ansible_bender"]["working_container"]["volumes"] == [f"{playbook_dir}:/src"]
    assert data["ansible_bender"]["target_image"]["name"] == "challet"
    assert data["ansible_bender"]["target_image"]["labels"] == {"x": "y"}
    assert data["ansible_bender"]["target_image"]["environment"] == {"asd": playbook_dir}


def test_b_m_empty():
    """ test that build and metadata are 'empty' when there are no vars """
    p = PbVarsParser(basic_playbook_path)
    b, m = p.get_build_and_metadata()
    assert isinstance(b, Build)
    assert isinstance(m, ImageMetadata)
    assert b.target_image is None
    assert b.cache_tasks is True
    assert b.layering is True


def test_set_all_params():
    """ test that we can set all the parameters """
    p = PbVarsParser(full_conf_pb_path)
    b, m = p.get_build_and_metadata()
    assert isinstance(b, Build)
    assert isinstance(m, ImageMetadata)

    assert b.base_image == "mona_lisa"
    assert b.layering == "yes-please"
    assert b.cache_tasks == "never!"
    assert b.ansible_extra_args == ["--some", "--args"]
    assert b.build_volumes == ["/c:/d"]
    assert b.target_image == "funky-mona-lisa"

    assert m.env_vars == {"z": "x"}
    assert m.volumes == ["/a"]
    assert m.working_dir == "/workshop"
    assert m.labels == {"x": "y"}
    assert m.cmd == "command -x -y z"
    assert m.user == "leonardo"
