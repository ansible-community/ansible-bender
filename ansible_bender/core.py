"""
Module to interact with Ansible, perform ansible-pleybook and extract metadata from Ansible vars

A sample configuration:

- hosts: all
  vars:
    ansible_bender:

      base_image: fedora:28

      target_image:
        name: asdqwe
        # configure environment variables: same name as ansible
        environment:
          X: Y
        labels:
          key: value
        # default working directory
        working_dir: /path

      working_container:
        user: 12345  # TODO
        volumes:
        - { src: /path/to/my/code, dest: /src:Z }

tasks:
  ...

"""
import datetime
import json
import os
import logging
import shlex
import subprocess
import tempfile
import shutil

import yaml

from ansible_bender.builders.base import Build, ImageMetadata

import ansible_bender
from ansible_bender import callback_plugins
from ansible_bender.constants import TIMESTAMP_FORMAT
from ansible_bender.exceptions import AbBuildUnsuccesful
from ansible_bender.utils import run_cmd, ap_command_exists, random_str

logger = logging.getLogger(__name__)
A_CFG_TEMPLATE = """\
[defaults]
retry_files_enabled = False
# when user is changed, ansible might not be able to write to /.ansible
remote_tmp = /tmp
callback_plugins={0}
callback_whitelist=snapshoter\n
"""


def run_playbook(playbook_path, inventory_path, a_cfg_path, connection, extra_variables=None,
                 ansible_args=None, debug=False, environment=None, try_unshare=True, provide_output=True):
    """
    run selected ansible playbook and return output from ansible-playbook run

    :param playbook_path:
    :param inventory_path:
    :param a_cfg_path:
    :param connection:
    :param extra_variables:
    :param ansible_args: list of str, extra arguments for a-p
    :param debug:
    :param environment:
    :param try_unshare: bool, do `buildah unshare` if uid > 0
    :param provide_output: bool, present output to user

    :return: output
    """
    ap = ap_command_exists()
    cmd_args = [
        ap,
        "-c", connection,

    ]
    if inventory_path:
        cmd_args += ["-i", inventory_path]
    if debug:
        cmd_args += ["-vvv"]
    if extra_variables:
        cmd_args += ["--extra-vars"] + \
                    [" ".join(
                        ["{}={}".format(k, v)
                         for k, v in extra_variables.items()]
                    )]
    if ansible_args:
        cmd_args += ansible_args
    cmd_args += [playbook_path]
    logger.debug("%s", " ".join(cmd_args))

    env = os.environ.copy()
    if environment:
        env.update(environment)
    if a_cfg_path:
        env["ANSIBLE_CONFIG"] = a_cfg_path

    if try_unshare and os.getuid() != 0:
        logger.info("we are running rootless, prepending `buildah unshare`")
        # rootless, we need to `buildah unshare` for sake of `buildah mount`
        # https://github.com/containers/buildah/issues/1271
        cmd_args = ["buildah", "unshare"] + cmd_args

    # TODO: does ansible have an API?
    try:
        return run_cmd(
            cmd_args,
            print_output=provide_output,
            save_output_in_exc=True,
            env=env,
            return_all_output=provide_output,
        )
    except subprocess.CalledProcessError as ex:
        raise AbBuildUnsuccesful("ansible-playbook execution failed: %s" % ex, ex.output)


class AnsibleRunner:
    """
    Run ansible on provided artifact using the Builder interface
    """

    def __init__(self, playbook_path, builder, build, debug=False):
        self.build_i = build
        self.pb = playbook_path
        self.builder = builder
        self.debug = debug

    def _create_inventory_file(self, fd, python_interpreter):
        fd.write(
            '%s ansible_connection="%s" ansible_python_interpreter="%s"\n' % (
                self.builder.ansible_host,
                self.builder.ansible_connection,
                python_interpreter
            )
        )

    def _create_ansible_cfg(self, fd):
        callback_plugins_dir = os.path.dirname(callback_plugins.__file__)
        fd.write(A_CFG_TEMPLATE.format(callback_plugins_dir))

    def _get_path_our_site(self):
        """ return a path to a directory which contains ansible_bender installation """
        # pip in Fedora installs to /usr/local which is on default pythonpath but when ansible invokes
        # the callback plugin, that directory is not on sys.path: wat?
        # hence, let's add the site ab is installed in to sys.path
        return os.path.dirname(os.path.dirname(ansible_bender.__file__))

    def build(self, db_path):
        """
        run the playbook against the container

        :param db_path, str, path to ab's database

        :return: str, output
        """
        tmp = tempfile.mkdtemp(prefix="ab")

        pythonpath = os.environ.get("PYTHONPATH", "")
        site_path = self._get_path_our_site()
        if pythonpath:
            pythonpath = f"{site_path}:{pythonpath}"
        else:
            pythonpath = site_path

        try:
            environment = {
                "AB_BUILD_ID": self.build_i.build_id,
                "AB_DB_PATH": db_path,
                "PYTHONPATH": pythonpath,  # TODO write an e2e test for this
            }
            inv_path = os.path.join(tmp, "inventory")
            logger.info("creating inventory file %s", inv_path)
            with open(inv_path, "w") as fd:
                self._create_inventory_file(fd, self.build_i.python_interpreter)
            a_cfg_path = os.path.join(tmp, "ansible.cfg")
            with open(a_cfg_path, "w") as fd:
                self._create_ansible_cfg(fd)
            extra_args = None
            if self.build_i.ansible_extra_args:
                extra_args = shlex.split(self.build_i.ansible_extra_args)
            return run_playbook(self.pb, inv_path, a_cfg_path, self.builder.ansible_connection,
                                debug=self.debug, environment=environment, ansible_args=extra_args)
        finally:
            shutil.rmtree(tmp)


class PbVarsParser:
    def __init__(self, playbook_path):
        """
        :param playbook_path: str, path to playbook
        """
        self.playbook_path = playbook_path
        self.build = Build()
        self.metadata = ImageMetadata()
        self.build.metadata = self.metadata

    def expand_pb_vars(self):
        """
        populate vars from a playbook, defined in vars section

        :return: dict
        """
        with open(self.playbook_path) as fd:
            d = yaml.safe_load(fd)

        try:
            # TODO: process all the plays
            d = d[0]
        except IndexError:
            raise RuntimeError("Invalid playbook, can't access the first document.")

        if "vars" not in d:
            return {}

        tmp = tempfile.mkdtemp(prefix="ab")
        json_data_path = os.path.join(tmp, "j.json")
        # TODO: implement loading vars from a file (include_vars)
        pb = {
            "hosts": "localhost",
            "vars": {
                "ab_vars": d["vars"],
            },
            "vars_files": d.get("vars_files", []),
            "gather_facts": False,
            "tasks": [
                {"debug": {"msg": "{{ ab_vars }}"}},
                {
                    "copy": {
                        "dest": json_data_path,
                        "content": '{{ ab_vars }}'
                    }
                }
            ]
        }
        i_path = os.path.join(tmp, "i")
        with open(i_path, "w") as fd:
            fd.write("localhost ansible_connection=local")

        tmp_pb_path = os.path.join(tmp, "p.yaml")
        with open(tmp_pb_path, "w") as fd:
            yaml.safe_dump([pb], fd)

        playbook_base = os.path.basename(self.playbook_path).split(".", 1)[0]
        timestamp = datetime.datetime.now().strftime(TIMESTAMP_FORMAT)
        symlink_name = f".{playbook_base}-{timestamp}-{random_str()}.yaml"
        playbook_dir = os.path.dirname(self.playbook_path)
        symlink_path = os.path.join(playbook_dir, symlink_name)
        os.symlink(tmp_pb_path, symlink_path)

        try:
            run_playbook(symlink_path, i_path, None, connection="local", try_unshare=False)

            with open(json_data_path) as fd:
                return json.load(fd)
        finally:
            os.unlink(symlink_path)
            shutil.rmtree(tmp)

    def process_pb_vars(self, playbook_vars):
        """
        accept variables from the playbook and update the Build and ImageMetadata objects with them

        :param playbook_vars: dict with all the playbook variables
        :return:
        """
        try:
            bender_data = playbook_vars["ansible_bender"]
        except KeyError:
            logger.info("no bender data found in the playbook")
            return
        self.metadata.update_from_configuration(bender_data.get("target_image", {}))
        self.build.update_from_configuration(bender_data)

    def get_build_and_metadata(self):
        """
        extra vars from the selected playbook

        :return: Build(), ImageMetadata()
        """
        data = self.expand_pb_vars()

        self.process_pb_vars(data)

        return self.build, self.metadata
