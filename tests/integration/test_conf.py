import getpass

from ansible_bender.builders.base import Build, ImageMetadata
from ansible_bender.core import PbVarsParser

from tests.spellbook import b_p_w_vars_path, basic_playbook_path, full_conf_pb_path


def test_expand_pb_vars():
    p = PbVarsParser(b_p_w_vars_path)
    data = p.expand_pb_vars()
    assert data == {"key": "value", "key2": getpass.getuser()}


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
