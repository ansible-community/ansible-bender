"""
Functional tests for configuration of a build
"""
import json
import logging
import subprocess

import pytest

from ansible_bender.builders.buildah_builder import buildah

from tests.spellbook import b_p_w_vars_path, p_w_vars_files_path, data_dir, basic_playbook_path, playbook_with_unknown_keys
from ..conftest import ab


logger = logging.getLogger("ansible_bender")


def test_basic(tmpdir):
    cmd = ["build", b_p_w_vars_path]
    ab(cmd, str(tmpdir))

    try:
        cmd = ["inspect", "--json"]
        ab_inspect_data = json.loads(ab(cmd, str(tmpdir), return_output=True))

        assert ab_inspect_data["base_image"] == "quay.io/biocontainers/python:3"
        assert ab_inspect_data["build_id"] == "1"
        assert ab_inspect_data['build_volumes'] == [f'{data_dir}:/src:Z']
        assert ab_inspect_data['builder_name'] == "buildah"
        assert len(ab_inspect_data['layers']) == 3
        assert ab_inspect_data["metadata"]["labels"] == {"x": "y"}
        assert ab_inspect_data["metadata"]["env_vars"] == {"asd": data_dir}
        assert ab_inspect_data["playbook_path"] == b_p_w_vars_path
        assert ab_inspect_data["pulled"] is False
        assert ab_inspect_data["target_image"] == "challet"

        last_layer_id = ab_inspect_data["layers"][-1]["layer_id"]
        cmd = ["podman", "inspect", "--type", "image", last_layer_id]
        inspect_data = json.loads(subprocess.check_output(cmd))[0]
        # "RepoTags": [
        #     "docker.io/library/python:3-alpine"
        # ],
        assert inspect_data["RepoTags"][0]

        cmd = ["podman", "inspect", "--type", "image", "challet"]
        inspect_data = json.loads(subprocess.check_output(cmd))[0]

        # buildah 1.12 adds this: `{'io.buildah.version': '1.12.0'}`
        assert inspect_data["Config"]["Labels"]["x"] == "y"
        assert f"asd={data_dir}" in inspect_data["Config"]["Env"]
        assert inspect_data["Config"]["WorkingDir"] == "/src"
    finally:
        try:
            buildah("rmi", ["challet"])  # FIXME: use builder interface instead for sake of other backends
        except subprocess.CalledProcessError as ex:
            print(ex)


def test_with_vars_files(tmpdir):
    cmd = ["build", p_w_vars_files_path]
    ab(cmd, str(tmpdir))

    try:
        cmd = ["inspect", "--json"]
        ab_inspect_data = json.loads(ab(cmd, str(tmpdir), return_output=True))

        assert ab_inspect_data["base_image"] == "quay.io/biocontainers/python:3"
        assert ab_inspect_data["build_id"] == "1"
        assert ab_inspect_data['builder_name'] == "buildah"
        assert len(ab_inspect_data['layers']) == 3
        assert ab_inspect_data["metadata"]["labels"] == {"x": "y"}
        assert ab_inspect_data["metadata"]["env_vars"] == {"key": "env", "path": "/etc/passwd"}
        assert ab_inspect_data["playbook_path"] == p_w_vars_files_path
        assert ab_inspect_data["pulled"] is False
        assert ab_inspect_data["target_image"] == "with-vars-files"
    finally:
        try:
            buildah("rmi", ["with-vars-files"])  # FIXME: use builder interface instead for sake of other backends
        except subprocess.CalledProcessError as ex:
            print(ex)

def test_with_inventory_file(tmpdir):
    playbook_path = data_dir + "/projects/playbook_and_inventory/playbook.yml"
    inventory_path = data_dir + "/projects/playbook_and_inventory/hosts.ini"
    cmd = ["build", "--inventory", inventory_path, playbook_path]
    ab(cmd, str(tmpdir))

    try:
        cmd = ["inspect", "--json"]
        ab_inspect_data = json.loads(ab(cmd, str(tmpdir), return_output=True))

        assert ab_inspect_data["base_image"] == "docker.io/python:3-alpine"
        assert ab_inspect_data["target_image"] == "playbook-and-inventory"
    finally:
        try:
            buildah("rmi", ["playbook-and-inventory"])  # FIXME: use builder interface instead for sake of other backends
        except subprocess.CalledProcessError as ex:
            print(ex)


def test_basic_build_errr(tmpdir):
    cmd = ["build", basic_playbook_path]
    with pytest.raises(subprocess.CalledProcessError) as ex:
        ab(cmd, str(tmpdir), return_output=True)
    e = ex.value.stdout
    assert "Failed validating 'type' in schema['properties']['base_image']:" in e
    assert "There was an error during execution: None is not of type 'string'" in e


def test_unknown_key_error(tmpdir):
    cmd = ["build", playbook_with_unknown_keys]
    with pytest.raises(subprocess.CalledProcessError) as ex:
        ab(cmd, str(tmpdir), return_output=True)
    assert "Additional properties are not allowed" in ex.value.stdout

