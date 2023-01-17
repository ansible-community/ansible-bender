import pytest

from ansible_bender.core import AnsibleVarsParser

# def test_host_can_parse_playbook_vars():
#     playbook_path = "tests/data/test_playbook/playbook_vars/playbook.yml"
#     hosts = Hosts(playbook_path)
#     host = hosts.first()
#     assert host.get_vars() == {}

# def test_host_can_parse_group_and_host_vars():
#     assert False

def test_can_parse_vars_with_no_inventory_no_config():
    playbook_path = "tests/data/projects/playbook_only/playbook.yml"
    vars_parser = AnsibleVarsParser(playbook_path)
    
    build, metadata = vars_parser.get_build_and_metadata()
    
    assert build.base_image == "docker.io/python:3-alpine"
    assert build.target_image == "a-very-nice-image"
    assert len(build.build_volumes) == 1

    assert metadata.working_dir == "/src"
    assert len(metadata.env_vars) == 1

def test_can_parse_vars_when_cfg_specifies_inventory():
    playbook_path = "tests/data/projects/cfg_specifies_inventory/playbook.yml"
    vars_parser = AnsibleVarsParser(playbook_path)

    build, metadata = vars_parser.get_build_and_metadata()

    assert build.base_image == "docker.io/python:3-alpine"
    assert build.target_image == "a-very-nice-image"
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

    assert metadata.working_dir == "/tmp"
    assert len(metadata.env_vars) == 1