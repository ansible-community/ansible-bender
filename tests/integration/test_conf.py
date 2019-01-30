import getpass

from ansible_bender.builders.base import Build, ImageMetadata
from ansible_bender.core import get_build_and_metadata_from_pb, expand_pb_vars

from tests.spellbook import b_p_w_vars_path


def test_expand_pb_vars():
    data = expand_pb_vars(b_p_w_vars_path)
    assert data == {"key": "value", "key2": getpass.getuser()}

def test_get_b_m():
    b, m = get_build_and_metadata_from_pb(b_p_w_vars_path)
    assert isinstance(b, Build)
    assert isinstance(m, ImageMetadata)
