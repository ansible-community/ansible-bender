import os
import logging
import subprocess
import tempfile
import shutil

from ansible_bender.exceptions import AbBuildUnsuccesful
from ansible_bender.utils import run_cmd, ap_command_exists


logger = logging.getLogger(__name__)


def run_playbook(playbook_path, inventory_path, a_cfg_path, connection, extra_variables=None,
                 ansible_args=None, debug=False):
    ap_command_exists()
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
    try:
        run_cmd(
            cmd_args,
            # FIXME: fails with 'exec: \"runc\": executable file not found in $PATH'
            # env={"ANSIBLE_CONFIG": a_cfg_path}
            print_output=True
        )
    except subprocess.CalledProcessError as ex:
        raise AbBuildUnsuccesful("ansible-playbook execution failed: %s" % ex)


class AnsibleRunner:
    """
    Run ansible on provided artifact using the Builder interface
    """

    def __init__(self, playbook_path, builder, debug=False):
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
        fd.write(
            """
            [defaults]
            retry_files_enabled = False
            # when user is changed, ansible might not be able to write to /.ansible
            remote_tmp = /tmp
            """
        )

    def build(self, python_interpreter="/usr/bin/python3"):
        """
        perform the build

        :return:
        """
        tmp = tempfile.mkdtemp(prefix="ab")
        try:
            inv_path = os.path.join(tmp, "inventory")
            logger.info("creating inventory file %s", inv_path)
            with open(inv_path, "w") as fd:
                self._create_inventory_file(fd, python_interpreter)
            # FIXME: do this and get rid of the retry file
            # a_cfg_path = os.path.join(tmp, "ansible.cfg")
            # with open(a_cfg_path, "w") as fd:
            #     self._create_ansible_cfg(fd)
            run_playbook(self.pb, inv_path, None, self.builder.ansible_connection,
                         debug=self.debug)
        finally:
            shutil.rmtree(tmp)
