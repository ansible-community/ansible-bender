"""
Tests for ansible invocation
"""
import pytest
from flexmock import flexmock

from ansible_bender import utils
from ansible_bender.core import run_playbook
from tests.spellbook import C7_AP_VER_OUT


def test_ansibles_python():
    flexmock(utils, run_cmd=lambda *args, **kwargs: C7_AP_VER_OUT),
    with pytest.raises(RuntimeError) as ex:
        run_playbook(None, None, None, None)
    assert str(ex.value).startswith(
        "ansible-bender is written in python 3 and does not work in python 2,\n")
