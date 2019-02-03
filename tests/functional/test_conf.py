"""
Functional tests for configuration of a build
"""
import json
import logging

from tests.spellbook import b_p_w_vars_path
from ..conftest import ab


logger = logging.getLogger("ansible_bender")


def test_basic(tmpdir):
    cmd = ["build", b_p_w_vars_path]
    ab(cmd, str(tmpdir))

    cmd = ["inspect", "--json"]
    ab_inspect_data = json.loads(ab(cmd, str(tmpdir), return_output=True))
    import ipdb; ipdb.set_trace()
