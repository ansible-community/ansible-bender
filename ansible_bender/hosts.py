import configparser
import os

from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.parsing.dataloader import DataLoader
from ansible_bender.conf import Build, ImageMetadata

from ansible_bender.core import PbVarsParser

class AnsibleVarParser:
    """
    AnsibleVarParser is used to parse the ansible variables from the playbook and inventory
    This class attempts to use the ansible API to parse the variables
    If the inventory is not specified, the class attempts to find the inventory file
    If the inventory is not found, the class will fall back to PbVarsParser to parse the variables
    """

    # Prefix for ansible_bender variables
    _variable_prefix = "ansible_bender_"

    _inventory_path = None

    _playbook_path = None

    build: Build = Build()

    metadata: ImageMetadata = ImageMetadata()

    _hosts: dict = {}

    def __init__(self, playbook_path, inventory_path = None) -> None:
        self._base_dir = os.path.dirname(playbook_path)
        self._playbook_path = playbook_path
        self._inventory_path = inventory_path if inventory_path else self._find_inventory_path()

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

    def _get_vars_from_playbook(self, host_name) -> dict:
        """
        Parse the playbook variables related to the ansible_bender information
        """
        playbook_variables = {}

        try:
            for host in self._hosts_in_playbook:
                if host.get("hosts") == host_name:
                    for key, value in host.items():
                        if str(key).startswith(self._variable_prefix):
                            new_key = key.replace(self._variable_prefix, "")
                            playbook_variables[new_key] = value
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

            for key, value in all_vars_for_host.items():
                if str(key).startswith(self._variable_prefix):
                    # Assume that ansible API has already 
                    # pulled variables with correct precedence
                    new_key = key.replace(self._variable_prefix, "")
                    ansible_variables[new_key] = value                                             
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