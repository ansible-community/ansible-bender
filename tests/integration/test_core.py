"""
Tests for ansible invocation
"""
import pytest
from flexmock import flexmock

from ansible_bender import utils
from ansible_bender.core import run_playbook
from ansible_bender.core import AnsibleVarsParser
from tests.spellbook import C7_AP_VER_OUT


def test_ansibles_python():
    flexmock(utils, run_cmd=lambda *args, **kwargs: C7_AP_VER_OUT),
    with pytest.raises(RuntimeError) as ex:
        run_playbook(None, None, None, None)
    assert str(ex.value).startswith(
        "ansible-bender is written in python 3 and does not work in python 2,\n")

def test_can_specify_playbook_and_inventory():
    playbook_path = "tests/data/projects/playbook_and_inventory/playbook.yml"
    inventory_path = "tests/data/projects/playbook_and_inventory/hosts.ini"
    vars_parser = AnsibleVarsParser(playbook_path, inventory_path)

    build, metadata = vars_parser.get_build_and_metadata()

    assert build.base_image == "docker.io/python:3-alpine"
    assert build.target_image == "playbook-and-inventory"
    assert len(build.build_volumes) == 0

    assert metadata.working_dir == "/tmp"
    assert len(metadata.env_vars) == 1

def test_can_parse_vars_with_no_inventory_no_config():
    playbook_path = "tests/data/projects/playbook_only/playbook.yml"
    vars_parser = AnsibleVarsParser(playbook_path)
    
    build, metadata = vars_parser.get_build_and_metadata()
    
    assert build.base_image == "docker.io/python:3-alpine"
    assert build.target_image == "no-inv-no-cfg"
    assert len(build.build_volumes) == 1

    assert metadata.working_dir == "/src"
    assert len(metadata.env_vars) == 1

def test_can_parse_vars_when_cfg_specifies_inventory():
    playbook_path = "tests/data/projects/cfg_specifies_inventory/playbook.yml"
    vars_parser = AnsibleVarsParser(playbook_path)

    build, metadata = vars_parser.get_build_and_metadata()

    assert build.base_image == "docker.io/python:3-alpine"
    assert build.target_image == "cfg-specifies-inventory"
    assert len(build.build_volumes) == 1

    assert metadata.working_dir == "/src"
    assert len(metadata.env_vars) == 1

def test_can_parse_host_and_group_vars():
    playbook_path = "tests/data/projects/host_and_group_vars/playbook.yml"
    vars_parser = AnsibleVarsParser(playbook_path)

    build, metadata = vars_parser.get_build_and_metadata()

    assert build.base_image == "docker.io/python:3-alpine"
    assert build.target_image == "host_var_host1"
    assert len(build.build_volumes) == 1

    assert metadata.working_dir == "/tmp/host_and_group_vars"
    assert len(metadata.env_vars) == 1