"""
Module to interact with Ansible, perform ansible-playbook and extract metadata from Ansible vars

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
import copy
import datetime
import importlib
import json
import logging
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import uuid
import configparser

import jsonschema
import yaml

import ansible_bender
from ansible_bender import callback_plugins
from ansible_bender.conf import ImageMetadata, Build
from ansible_bender.constants import TIMESTAMP_FORMAT, TIMESTAMP_FORMAT_TOGETHER
from ansible_bender.exceptions import ABBuildUnsuccesful, ABValidationError
from ansible_bender.schema import PLAYBOOK_SCHEMA
from ansible_bender.utils import run_cmd, ap_command_exists, random_str, graceful_get, \
    is_ansibles_python_2

from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.parsing.dataloader import DataLoader
from ansible_bender.conf import Build, ImageMetadata

logger = logging.getLogger(__name__)
# callback_whitelist got renamed to callbacks_enabled in ansible
# drop callback_whitelist once 2.15 is released
# https://docs.ansible.com/ansible/latest/reference_appendices/config.html#callbacks-enabled
A_CFG_TEMPLATE = """\
[defaults]
# when user is changed, ansible might not be able to write to /.ansible
remote_tmp = /tmp
callback_plugins={0}
callback_whitelist=snapshoter\n
callbacks_enabled=snapshoter\n
"""


def run_playbook(playbook_path, inventory_path, a_cfg_path, connection, extra_variables=None,
                 ansible_args=None, debug=False, environment=None, try_unshare=True,
                 provide_output=True, log_stderr=False):
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
    :param log_stderr: bool, log errors coming from stderr to our logger

    :return: output
    """
    ap = ap_command_exists()
    if is_ansibles_python_2(ap):
        # I just realized it could work, we would just had to disable the
        # callback plugin: no caching and layering
        raise RuntimeError(
            "ansible-bender is written in python 3 and does not work in python 2,\n"
            f"it seems that {ap} is using python 2 - ansible-bender will not"
            "work in such environment\n"
        )
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
    env["ANSIBLE_RETRY_FILES_ENABLED"] = "0"
    if debug:
        env["ANSIBLE_STDOUT_CALLBACK"] = "debug"
    if environment:
        env.update(environment)
    if a_cfg_path:
        env["ANSIBLE_CONFIG"] = a_cfg_path

    if try_unshare and os.getuid() != 0:
        logger.info("we are running rootless, prepending `buildah unshare`")
        # rootless, we need to `buildah unshare` for sake of `buildah mount`
        # https://github.com/containers/buildah/issues/1271
        # the need for `--` https://github.com/containers/buildah/issues/1374
        cmd_args = ["buildah", "unshare", "--"] + cmd_args

    # ansible has no official python API, the API they have is internal and said to break compat
    try:
        return run_cmd(
            cmd_args,
            print_output=provide_output,
            save_output_in_exc=True,
            env=env,
            return_all_output=provide_output,
            log_stderr=log_stderr,
        )
    except subprocess.CalledProcessError as ex:
        raise ABBuildUnsuccesful("ansible-playbook execution failed: %s" % ex, ex.output)


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
        # pip in Fedora installs to /usr/local which is on default pythonpath
        # but when ansible invokes the callback plugin, that directory is not on sys.path: wat?
        # hence, let's add the site ab is installed in to sys.path
        return os.path.dirname(os.path.dirname(ansible_bender.__file__))

    def _correct_host_entries(self, playbook_path, tmpDir):
        """ Correct the host entries in the playbook and all imported playbooks """
        tmp_pb_path = os.path.join(tmpDir, "ab_" + str(uuid.uuid4()) + ".yaml")

        with open(playbook_path, "r") as fd_r:
            pb_dict = yaml.safe_load(fd_r)
            
        for idx, doc in enumerate(pb_dict):
            imported_playbook = doc.get("import_playbook")
            if imported_playbook:
                import_base_path = os.path.dirname(playbook_path)
                imported_playbook_path = os.path.join(import_base_path, imported_playbook)
                logger.debug("Encountered import_playbook, correcting hosts entries in imported file: %s", imported_playbook_path)
                doc["import_playbook"] = self._correct_host_entries(imported_playbook_path, tmpDir)
            else:
                host = doc["hosts"]
                logger.debug("play[%s], host = %s", idx, host)
                doc["hosts"] = self.builder.ansible_host

        with open(tmp_pb_path, "w") as fd:
            yaml.safe_dump(pb_dict, fd)

        return tmp_pb_path
    
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

            tmp_pb_path = self._correct_host_entries(self.pb, tmp)
            playbook_base = os.path.basename(self.pb).split(".", 1)[0]
            timestamp = datetime.datetime.now().strftime(TIMESTAMP_FORMAT)
            symlink_name = f".{playbook_base}-{timestamp}-{random_str()}.yaml"
            playbook_dir = os.path.dirname(self.pb)
            symlink_path = os.path.join(playbook_dir, symlink_name)
            os.symlink(tmp_pb_path, symlink_path)

            extra_args = None
            try:
                if self.build_i.ansible_extra_args:
                    extra_args = shlex.split(self.build_i.ansible_extra_args)
                return run_playbook(
                    symlink_path, inv_path, a_cfg_path, self.builder.ansible_connection,
                    debug=self.debug, environment=environment, ansible_args=extra_args
                )
            finally:
                os.unlink(symlink_path)
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

        :return: dict with the content of ansible_bender var
        """
        with open(self.playbook_path) as fd:
            plays = yaml.safe_load(fd)

        for play in plays[1:]:
            bender_vars = graceful_get(play, "vars", "ansible_bender")
            if bender_vars:
                logger.warning("Variables are loaded only from the first play.")

        try:
            # we care only about the first play, we don't want to merge dicts
            d = plays[0]
        except IndexError:
            raise RuntimeError("Invalid playbook, can't access the first document.")

        bender_vars = graceful_get(d, "vars", "ansible_bender")
        if not bender_vars:
            logger.info("no bender data found in the playbook")
            return {}

        tmp = tempfile.mkdtemp(prefix="ab")
        json_data_path = os.path.join(tmp, "j.json")

        # we cannot use "vars" variable because the variables are not expanded in there
        pb_vars = copy.deepcopy(d["vars"])
        while True:
            # just in case the variable is already defined
            timestamp = datetime.datetime.now().strftime(TIMESTAMP_FORMAT_TOGETHER)
            ab_vars_key = f"ab_vars_{timestamp}"
            if ab_vars_key not in pb_vars:
                logger.debug("ab vars key = %s", ab_vars_key)
                pb_vars[ab_vars_key] = d["vars"]
                break
        jinja_pb_vars_key = '{{ %s }}' % ab_vars_key
        pb = {
            "name": "Let Ansible expand variables",
            "hosts": "localhost",
            "vars": pb_vars,
            "vars_files": d.get("vars_files", []),
            "gather_facts": False,
            "tasks": [
                {"debug": {"msg": jinja_pb_vars_key}},
                {
                    "copy": {
                        "dest": json_data_path,
                        "content": jinja_pb_vars_key
                    }
                }
            ]
        }

        i_path = os.path.join(tmp, "i")
        with open(i_path, "w") as fd:
            fd.write("localhost ansible_connection=local")

        # json is easier to parse than yaml
        tmp_pb_path = os.path.join(tmp, "p.json")
        with open(tmp_pb_path, "w") as fd:
            json.dump([pb], fd)

        playbook_base = os.path.basename(self.playbook_path).split(".", 1)[0]
        symlink_name = f".{playbook_base}-{timestamp}-{random_str()}.yaml"
        playbook_dir = os.path.dirname(self.playbook_path)
        symlink_path = os.path.join(playbook_dir, symlink_name)
        os.symlink(tmp_pb_path, symlink_path)

        # yeah, ansible is not very smart for connection=local
        args = ["-e", f"ansible_python_interpreter={sys.executable}"]

        try:
            run_playbook(symlink_path, i_path, None, connection="local", try_unshare=False,
                         provide_output=False, log_stderr=True, ansible_args=args)

            with open(json_data_path) as fd:
                return json.load(fd)["ansible_bender"]
        finally:
            os.unlink(symlink_path)
            shutil.rmtree(tmp)

    def process_pb_vars(self, bender_data):
        """
        accept variables from the playbook and update the Build and ImageMetadata objects with them

        :param bender_data: dict with the content of ansible_bender vars
        :return:
        """
        if not bender_data:
            return
        try:
            # validation to error out unknown keys in /vars/ansible_bender
            jsonschema.validate(bender_data, PLAYBOOK_SCHEMA)
        except jsonschema.ValidationError as validation_error:
            if validation_error.validator == "type":
                # error is due to invalid value datatype
                path = "/" + "/".join(validation_error.path)
                expected_types = validation_error.validator_value
                if isinstance(validation_error.validator_value, list):
                    expected_types = ", ".join(validation_error.validator_value)
                message = f"variable {path} is set to {validation_error.instance}" \
                          f", which is not of type {expected_types}"
                raise ABValidationError(message) from validation_error
            else:
                # error is due to absence of a required key, unknown keys playbook or any other kind
                raise ABValidationError(validation_error.message) from validation_error

        self.metadata.update_from_configuration(bender_data.get("target_image", {}))
        self.build.update_from_configuration(bender_data)

    def get_build_and_metadata(self):
        """
        extra vars from the selected playbook

        :return: Build(), ImageMetadata()
        """
        bender_data = self.expand_pb_vars()

        self.process_pb_vars(bender_data)

        return self.build, self.metadata


class AnsibleVarsParser:
    """
    AnsibleVarParser is used to parse the ansible variables from the playbook and inventory
    This class attempts to use the ansible API to parse the variables
    If the inventory is not specified, the class attempts to find the inventory file
    If the inventory is not found, the class will fall back to PbVarsParser to parse the variables
    """

    # Prefix for ansible_bender variables
    _variable_prefix = "ansible_bender"

    _inventory_path = None

    _playbook_path = None

    _loader: DataLoader = None

    _inventory: InventoryManager = None

    _variable_manager: VariableManager = None

    _hosts_in_playbook: list = None

    _hosts: dict = {}

    build: Build = None

    metadata: ImageMetadata = None

    def __init__(self, playbook_path, inventory_path = None) -> None:
        self._base_dir = os.path.dirname(playbook_path)
        self._playbook_path = playbook_path
        self._inventory_path = inventory_path if inventory_path else self._find_inventory_path()
        self.build = Build()
        self.metadata = ImageMetadata()
        self.build.metadata = self.metadata

    def __getitem__(self, key):
        return self._hosts[key]

    def _find_ansible_cfg(self) -> str:
        """
        Find the ansible.cfg file
        Precendence: https://docs.ansible.com/ansible/latest/reference_appendices/config.html
        """
        # Check environment variable
        if "ANSIBLE_CONFIG" in os.environ:
            return os.environ["ANSIBLE_CONFIG"]

        # Check in self._base_dir (playbook directory)
        if os.path.isfile(os.path.join(self._base_dir, "ansible.cfg")):
            return os.path.join(self._base_dir, "ansible.cfg")

        # Check in home directory
        if os.path.isfile(os.path.join(os.path.expanduser("~"), ".ansible.cfg")):
            return os.path.join(os.path.expanduser("~"), ".ansible.cfg")

        # Check in /etc/ansible/ansible.cfg
        if os.path.isfile("/etc/ansible/ansible.cfg"):
            return "/etc/ansible/ansible.cfg"

        # No ansible.cfg file found
        return None

    def _find_inventory_path(self) -> str:
        """
        Get the inventory path from either
        1. ansible.cfg
        2. the default ansible inventory location (/etc/ansible/hosts)
        """
        ansible_cfg_path = self._find_ansible_cfg()

        if ansible_cfg_path:
            return self._get_inventory_from_ansible_cfg(ansible_cfg_path)
        else:
            if os.path.isfile("/etc/ansible/hosts"):
                return"/etc/ansible/hosts"

        return None

    def _get_inventory_from_ansible_cfg(self, ansible_cfg_path) -> str:
        """
        Get the inventory path from the ansible.cfg file
        """
        config = configparser.ConfigParser()
        config.read(ansible_cfg_path)
        inv_path = config.get("defaults", "inventory", fallback=None)

        # Possible to have an ansible.cfg file without an inventory path
        if inv_path is None:
            return None

        # Inventory path can be absolute or relative in ansible.cfg
        if os.path.isabs(inv_path):
            return inv_path
        else:
            return os.path.join(os.path.dirname(ansible_cfg_path), inv_path)

    def _get_host_names(self, hosts) -> list:
        """
        Parse the hosts from the playbook
        """
        parsed_host_information = []

        for host in hosts:
            parsed_host_information.append(host.get("hosts"))

        return parsed_host_information

    def _extract_variables(self, ansible_variables, variables):
        """
        Convinience function to get the variables from the variables dictionary
        Gets the ansible_bender variables and the prepended variables
        """

        if variables is None:
            return ansible_variables

        for key, value in variables.items():
            if str(key).startswith(self._variable_prefix):
                    # Assume that ansible API has already 
                    # pulled variables with correct precedence
                new_key = key.replace(self._variable_prefix, "")

                    # key can be prepended with ansible_bender_ or ansible_bender
                    # if it is prepended with ansible_bender_, remove the _
                if new_key.startswith("_"):
                    new_key = new_key[1:]

                    # If the new_key is blank
                    # then the "ansible_bender" variable was used
                    # Add the variables to the ansible_variables
                if new_key == "":
                    ansible_variables.update(value)
                else:
                    ansible_variables[new_key] = value

        return ansible_variables

    def _get_vars_from_playbook(self, host_name) -> dict:
        """
        Parse the playbook variables related to the ansible_bender information
        """
        playbook_variables = {}

        try:
            for host in self._hosts_in_playbook:
                if host.get("hosts") == host_name:
                    playbook_variables = self._extract_variables(playbook_variables, host.get("vars"))
        except Exception as e:
            print("Error getting playbook variables for host: " + host_name + " - " + str(e))
            pass

        return playbook_variables

    def _get_vars_for_host(self, host_name) -> dict:
        """
        Parse the host variables from the inventory information
        """
        ansible_variables = {}
        try:
            ansible_host = self._inventory.get_host(host_name)
            all_vars_for_host = self._variable_manager.get_vars(host=ansible_host, 
                                                            include_hostvars=True, 
                                                            include_delegate_to=True)

            # find prepended variables
            self._extract_variables(ansible_variables, all_vars_for_host)                
        except Exception as e:
            print("Error getting host and group vars for host: " + host_name + " - " + str(e))
            pass

        # Append the playbook variables to the ansible variables
        ansible_variables.update(self._get_vars_from_playbook(host_name))

        return ansible_variables

    
    def get_build_and_metadata(self):
        """
        Find all hosts in the playbook and get their variables
        return the build and imagemetadata information
        """
        if self._inventory_path:
            # Ansible API objects used to pull variables
            relative_playbook_file_path = os.path.basename(self._playbook_path)
            self._loader = DataLoader()
            self._loader.set_basedir(self._base_dir)
            self._inventory = InventoryManager(loader=self._loader, sources=self._inventory_path)
            self._variable_manager = VariableManager(loader=self._loader, inventory=self._inventory)
            self._hosts_in_playbook = self._loader.load_from_file(relative_playbook_file_path)

            host_names = self._get_host_names(self._hosts_in_playbook)
            for host_name in host_names:
                ansible_vars = self._get_vars_for_host(host_name)
                self._hosts[host_name] = ansible_vars

            # We only support one host in the playbook
            host = self._hosts[list(self._hosts)[0]] if len(self._hosts) > 0 else None

            if not host:
                raise Exception("No hosts found in the playbook")

            self.metadata.update_from_configuration(host.get("target_image", {}))
            self.build.update_from_configuration(host)
        else:
            # At this point
            # 1. No inventory was provided
            # 2. No ansible.cfg file was found with inventory information
            # 3. No default inventory file was found
            # So forget about using the ansible API to get variables
            # Just manually parse the playbook
            pb_vars_p = PbVarsParser(self._playbook_path)
            self.build, self.metadata = pb_vars_p.get_build_and_metadata()

        return self.build, self.metadata
