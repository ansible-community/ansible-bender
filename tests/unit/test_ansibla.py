import importlib
from functools import partial
from pathlib import Path

import pytest
from flexmock import flexmock

from ansible_bender.core import PbVarsParser
from ansible_bender.exceptions import ABValidationError


def mock_read_text(return_val=None, raise_exc=False):
    if raise_exc:
        def _f():
            raise FileNotFoundError()
        flexmock(Path, read_text=_f)
    else:
        flexmock(Path, read_text=lambda: return_val)


def mock_import_module(raise_exc=False):
    if raise_exc:
        def _f(name, package=None):
            raise ModuleNotFoundError()
        flexmock(importlib, import_module=_f)
    else:
        flexmock(importlib, import_module=lambda name: None)


@pytest.mark.parametrize("mock_r_t,mock_i_m,should_raise", (
    (
        partial(mock_read_text, "1"),
        partial(mock_import_module, False),
        False
    ),
    (
        partial(mock_read_text, "1"),
        partial(mock_import_module, True),
        True
    ),
    (
        partial(mock_read_text, "0"),
        partial(mock_import_module, False),
        False
    ),
    (
        partial(mock_read_text, "0"),
        partial(mock_import_module, True),
        True
    ),
    (
        partial(mock_read_text, None, True),
        partial(mock_import_module, False),
        False
    ),
))
def test_ansible_selinux_workaround(mock_r_t, mock_i_m, should_raise):
    mock_r_t()
    mock_i_m()
    p = PbVarsParser("")
    if should_raise:
        with pytest.raises(RuntimeError) as ex:
            p._check_selinux_iz_gud()
        assert "libselinux" in str(ex.value)
    else:
        p._check_selinux_iz_gud()


@pytest.mark.parametrize("di, error_message", (
    (
        {"target_image": {"user": {}}},
        "variable /target_image/user is set to {}, which is not of type string, null"
    ),
    (
        {"target_image": {"volumes": {"A": "B"}}},
        "variable /target_image/volumes is set to {'A': 'B'}, which is not of type array"
    ),
    (
        {"target_image": {"environment": ["A=B"]}},
        "variable /target_image/environment is set to ['A=B'], which is not of type object"
    ),
    (
        {"target_image": {"environment": "A=B"}},
        "variable /target_image/environment is set to A=B, which is not of type object"
    ),
))
def test_validation(di, error_message):
    p = PbVarsParser("")
    with pytest.raises(ABValidationError) as ex:
        p.process_pb_vars(di)
    assert error_message in str(ex)
