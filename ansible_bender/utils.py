"""
Utility functions. This module can't depend on anything within ab.
"""
import logging
import os
import random
import re
import shutil
import string
import subprocess
import threading

from ansible_bender.constants import OUT_LOGGER


logger = logging.getLogger(__name__)
out_logger = logging.getLogger(OUT_LOGGER)


def graceful_get(d, *keys, default=None):
    """
    recursively obtain value from nested dict

    :param d: dict
    :param keys:
    :param default: a value to return by default

    :return: value or None
    """
    response = d
    for k in keys:
        try:
            response = response[k]
        except (KeyError, AttributeError, TypeError) as ex:
            logger.debug("can't obtain %s: %s", k, ex)
            return default
    return response


class StreamLogger(threading.Thread):
    def __init__(self, stream, print_output=False, log_level=logging.DEBUG, log_output=True, buffer=None):
        super().__init__(daemon=True)  # the threads should not linger
        self.stream = stream
        self.buffer = buffer  # to easily share output, both stdout & stderr
        self.output = []
        self.log_level = log_level
        self.log_output = log_output
        self.print_output = print_output

    def run(self):
        for line in self.stream:
            line = line.rstrip("\n")
            if self.buffer is not None:
                self.buffer.append(line)
            self.output.append(line)
            if self.log_output:
                logger.log(self.log_level, line)
            if self.print_output:
                out_logger.info(line)

    def get_output(self):
        return "\n".join(self.output)


def run_cmd(cmd, return_output=False, ignore_status=False, print_output=False, log_stderr=True,
            save_output_in_exc=True,
            log_output=True, return_all_output=False, **kwargs):
    """
    run provided command on host system using the same user as you invoked this code, raises
    subprocess.CalledProcessError if it fails

    :param cmd: list of str
    :param return_output: bool, return output of the command
    :param return_all_output: bool, return output including stderr
    :param ignore_status: bool, do not fail in case nonzero return code
    :param kwargs: pass keyword arguments to subprocess.check_* functions; for more info,
            please check `help(subprocess.Popen)`
    :param print_output: bool, print output via print()
    :param log_stderr: bool, log errors to stdout as ERROR level
    :param log_output: bool, print output of the command to logs
    :param save_output_in_exc: bool, add command output to exception in case of an error
    :return: None or str
    """
    logger.info('running command: "%s"', cmd)
    logger.debug('%s', " ".join(cmd))  # so you can easily copy/pasta
    whole_output = []
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True, **kwargs)
    o = StreamLogger(process.stdout, print_output=print_output, log_level=logging.DEBUG,
                     log_output=log_output, buffer=whole_output)
    stderr_log_lvl = logging.ERROR if log_stderr else logging.DEBUG
    e = StreamLogger(process.stderr, print_output=print_output, log_level=stderr_log_lvl, buffer=whole_output)
    o.start()
    e.start()
    process.wait()
    o.join()
    e.join()

    if process.returncode > 0:
        if ignore_status:
            if return_output:
                return o.get_output()
            else:
                return process.returncode
        else:
            out = ""
            errout = ""
            if save_output_in_exc:
                out = "\n".join(whole_output)
                errout = e.get_output()
            raise subprocess.CalledProcessError(cmd=cmd, returncode=process.returncode,
                                                stderr=errout, output=out)
    if return_all_output:
        return whole_output
    if return_output:
        return o.get_output()


class CommandDoesNotExistException(Exception):
    pass


def env_get_or_fail_with(env_name, err_msg):
    try:
        return os.environ[env_name]
    except KeyError:
        raise RuntimeError(err_msg)


def one_of_commands_exists(commands, exc_msg) -> str:
    """
    Verify that the provided command exists. Raise CommandDoesNotExistException in case of an
    error or if the command does not exist.

    :param commands: str, command to check (python 3 only)
    :param exc_msg: str, message of exception when command does not exist
    :return: str, the command which exists
    """
    found = False
    for command in commands:
        found = bool(shutil.which(command))  # py3 only
        if found:
            return command
    if not found:
        raise CommandDoesNotExistException(exc_msg)


def ap_command_exists():
    return one_of_commands_exists(
        ["ansible-playbook-3", "ansible-playbook"],
        "ansible-playbook command doesn't seem to be available on your system. "
        "It is usually available in 'ansible' package or follow the upstream instructions "
        "available at https://docs.ansible.com/ansible/latest/installation_guide/"
        "intro_installation.html#installation-guide"
    )


def buildah_command_exists():
    return one_of_commands_exists(
        ["buildah"],
        "buildah command doesn't seem to be available on your system. "
        "Please follow the upstream instructions "
        "available at https://github.com/projectatomic/buildah/blob/master/install.md"
    )


def podman_command_exists():
    return one_of_commands_exists(
        ["podman"],
        "podman command doesn't seem to be available on your system. "
        "Please follow the upstream instructions "
        "available at https://github.com/containers/libpod/blob/master/install.md"
    )


def git_command_exists():
    return one_of_commands_exists(
        ["git"],
        "git command is not available"
    )


def git_clone_to_path(repo_url, path, ref="master"):
    """
    clone repo provided as repo_url into directory specified as path

    :param repo_url: str
    :param path: str
    :param ref: str, git ref
    """
    run_cmd(["git", "clone", "--depth", "1", "-b", ref, repo_url, path])


def set_logging(
        logger_name="ansible_bender",
        level=logging.INFO,
        handler_class=logging.StreamHandler,
        handler_kwargs=None,
        format='%(asctime)s.%(msecs).03d %(filename)-17s %(levelname)-6s %(message)s',
        date_format='%H:%M:%S'):
    """
    Set personal logger for this library.

    :param logger_name: str, name of the logger
    :param level: int, see logging.{DEBUG,INFO,ERROR,...}: level of logger and handler
    :param handler_class: logging.Handler instance, default is StreamHandler (/dev/stderr)
    :param handler_kwargs: dict, keyword arguments to handler's constructor
    :param format: str, formatting style
    :param date_format: str, date style in the logs
    :return: logger instance
    """
    logger = logging.getLogger(logger_name)
    # do we want to propagate to root logger?
    # logger.propagate = False
    logger.setLevel(level)

    # don't readd handler
    if not [x for x in logger.handlers if isinstance(x, handler_class)]:
        handler_kwargs = handler_kwargs or {}
        handler = handler_class(**handler_kwargs)
        handler.setLevel(level)
        formatter = logging.Formatter(format, date_format)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def random_str(size=10):
    """
    create random string of selected size

    :param size: int, length of the string
    :return: the string
    """
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(size))


def is_ansibles_python_2(ap_exe: str) -> bool:
    """
    Discover whether ansible-playbook is using python 2.

    :param ap_exe: path to the python executable

    :return: True if it's 2
    """
    out = run_cmd([ap_exe, "--version"], log_stderr=True, return_output=True)

    # python version = 3.7.2
    reg = r"python version = (\d)"

    reg_grp = re.findall(reg, out)
    try:
        py_version = reg_grp[0]
    except IndexError:
        logger.warning("could not figure out which python is %s using", ap_exe)
        return False  # we don't know, fingers crossed
    if py_version == "2":
        logger.info("%s is using python 2", ap_exe)
        return True
    logger.debug("it seems that %s is not using python 2", ap_exe)
    return False
