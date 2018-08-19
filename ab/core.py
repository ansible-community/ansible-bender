import os
import logging
import tempfile
import shutil

from ab.utils import run_cmd

logger = logging.getLogger(__name__)


def run_playbook(playbook_path, inventory_path, a_cfg_path, connection, extra_variables=None,
                 ansible_args=None, debug=False):
    # TODO: make sure a-p is present on system
    cmd_args = [
        "ansible-playbook",
        "-i", inventory_path,
        "-c", connection,

    ]
    if debug:
        cmd_args += ["-vvvvv"]
    if extra_variables:
        cmd_args += ["--extra-vars"] + \
                    [" ".join(
                        ["{}={}".format(k, v)
                         for k, v in extra_variables.items()]
                    )]
    cmd_args += [playbook_path]
    logger.debug("%s", " ".join(cmd_args))
    # TODO: does ansible have an API?
    run_cmd(
        cmd_args,
        # FIXME: fails with 'exec: \"runc\": executable file not found in $PATH'
        # env={"ANSIBLE_CONFIG": a_cfg_path}
    )


class AnsibleRunner:
    """
    Run ansible on provided artifact using the Builder interface
    """

    # TODO: try to find the python interpreter inside
    def __init__(self, playbook_path, builder, python_interpreter="/usr/bin/python3",
                 debug=False):
        """
        :param debug: bool, provide debug output if True
        """
        self.pb = playbook_path
        self.builder = builder
        self.python_interpreter = python_interpreter
        self.debug = debug

    def _create_inventory_file(self, fd):
        fd.write(
            '%s ansible_connection="%s" ansible_python_interpreter="%s"\n' % (
                self.builder.ansible_host,
                self.builder.ansible_connection,
                self.python_interpreter
            )
        )

    def _create_ansible_cfg(self, fd):
        fd.write(
            """
            [defaults]
            retry_files_enabled = False
            # when user is changed, ansible might not be able to write to /.ansible
            remote_tmp = /tmp
            """
        )

    def build(self):
        """
        perform the build

        :return:
        """
        tmp = tempfile.mkdtemp(prefix="ab")
        try:
            inv_path = os.path.join(tmp, "inventory")
            with open(inv_path, "w") as fd:
                self._create_inventory_file(fd)
            a_cfg_path = os.path.join(tmp, "ansible.cfg")
            with open(a_cfg_path, "w") as fd:
                self._create_ansible_cfg(fd)
            run_playbook(self.pb, inv_path, a_cfg_path, self.builder.ansible_connection,
                         debug=self.debug)
        finally:
            shutil.rmtree(tmp)
