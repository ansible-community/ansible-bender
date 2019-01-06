import re

import pytest

from ansible_bender.db import generate_working_cont_name
from ansible_bender.utils import run_cmd


def test_run_cmd():
    assert "etc" in run_cmd(["ls", "-1", "/"], return_all_output=True)


@pytest.mark.parametrize("image_name,expected", (
    ("lojza", r"^lojza-\d{8}-\d{12}-cont$"),
    (
        "172.30.1.1:5000/myproject/just-built-ansible-bender:latest",
        r"^172-30-1-1-5000-myproject-just-built-ansible-bender-latest-\d{8}-\d{12}-cont$",
    ),
))
def test_gen_work_cont_name(image_name, expected):
    assert re.match(expected, generate_working_cont_name(image_name))
