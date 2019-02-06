"""
Functional tests for configuration of a build
"""
import json
import logging
import subprocess

from ansible_bender.builders.buildah_builder import buildah

from tests.spellbook import b_p_w_vars_path, p_w_vars_files_path
from ..conftest import ab


logger = logging.getLogger("ansible_bender")


def test_basic(tmpdir):
    cmd = ["build", b_p_w_vars_path]
    ab(cmd, str(tmpdir))

    try:
        cmd = ["inspect", "--json"]
        ab_inspect_data = json.loads(ab(cmd, str(tmpdir), return_output=True))
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
    finally:
        try:
            buildah("rmi", ["with-vars-files"])  # FIXME: use builder interface instead for sake of other backends
        except subprocess.CalledProcessError as ex:
            print(ex)
