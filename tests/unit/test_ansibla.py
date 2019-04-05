import importlib
from functools import partial
from pathlib import Path

import pytest
from flexmock import flexmock

from ansible_bender.core import PbVarsParser


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
