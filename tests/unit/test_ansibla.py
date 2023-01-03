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
