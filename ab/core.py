import os
import logging
import subprocess
import tempfile
import shutil


logger = logging.getLogger(__name__)


def run_playbook(playbook_path, inventory_path, connection, extra_variables=None,
                 ansible_args=None, debug=False):
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
    subprocess.check_call(cmd_args)


class AnsibleRunner:
    """
    Run ansible on provided artifact using the Builder interface
    """

    def __init__(self, playbook_path, builder, python_interpreter="/usr/bin/python3"):
        self.pb = playbook_path
        self.builder = builder
        self.python_interpreter = python_interpreter

    def _create_inventory_file(self, fd):
        fd.write(
            '%s ansible_connection="%s" ansible_python_interpreter="%s"\n' % (
                self.builder.ansible_host,
                self.builder.ansible_connection,
                self.python_interpreter
            )
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
            run_playbook(self.pb, inv_path, self.builder.ansible_connection)
        finally:
            shutil.rmtree(tmp)
