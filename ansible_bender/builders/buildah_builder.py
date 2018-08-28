import json
import logging
import subprocess

from ansible_bender.builders.base import Builder
from ansible_bender.utils import graceful_get, run_cmd, buildah_command_exists, podman_command_exists

logger = logging.getLogger(__name__)


def inspect_buildah_resource(resource_type, resource_id):
    try:
        i = run_cmd(["buildah", "inspect", "-t", resource_type, resource_id], return_output=True)
    except subprocess.CalledProcessError:
        logger.info("no such %s %s", resource_type, resource_id)
        return None
    metadata = json.loads(i)
    return metadata


def get_buildah_image_id(container_image):
    metadata = inspect_buildah_resource("image", container_image)
    return graceful_get(metadata, "FromImageID")


def pull_buildah_image(container_image):
    run_cmd(["podman", "pull", container_image])


def podman_run_cmd(container_image, cmd, log_stderr=True):
    """
    run provided command in selected container image using podman; raise exc when command fails

    :param container_image: str
    :param cmd: list of str
    :param log_stderr: bool, log errors to stdout as ERROR level
    :return: stdout output
    """
    return run_cmd(["podman", "run", "--rm", container_image] + cmd,
                   return_output=False, log_stderr=log_stderr)


def create_buildah_container(container_image, container_name, build_volumes=None, debug=False):
    """
    Create new buildah container according to spec.

    :param container_image: name of the image
    :param container_name: name of the container to work in
    :param build_volumes: list of str, bind-mount specification: ["/host:/cont", ...]
    :param debug: bool, make buildah print debug info
    """
    args = []
    if build_volumes:
        args += ["-v"] + build_volumes
    args += ["--name", container_name, container_image]
    # will pull the image by default if it's not present in buildah's storage
    buildah("from", args, debug=debug)


def configure_buildah_container(container_name, working_dir=None, env_vars=None,
                                labels=None, user=None, cmd=None, ports=None, volumes=None,
                                debug=False):
    """
    apply metadata on the container so they get inherited in an image

    :param container_name: name of the container to work in
    :param working_dir: str, path to a working directory within container image
    :param labels: dict with labels
    :param env_vars: dict with env vars
    :param cmd: str, command to run by default in the container
    :param user: str, username or uid; the container gets invoked with this user by default
    :param ports: list of str, ports to expose from container by default
    :param volumes: list of str; paths within the container which has data stored outside
                    of the container
    :param debug: bool, make buildah print debug info
    """
    config_args = []
    if working_dir:
        config_args += ["--workingdir", working_dir]
    if env_vars:
        for k, v in env_vars.items():
            config_args += ["-e", "%s=%s" % (k, v)]
    if labels:
        for k, v in labels.items():
            config_args += ["-l", "%s=%s" % (k, v)]
    if user:
        config_args += ["--user", user]
    if cmd:
        config_args += ["--cmd", cmd]
    if ports:
        for p in ports:
            config_args += ["-p", p]
    if volumes:
        for v in volumes:
            config_args += ["-v", v]
    if config_args:
        buildah("config", config_args + [container_name], debug=debug)
    return container_name


def buildah(command, args_and_opts, print_output=False, debug=False):
    cmd = ["buildah"]
    if debug:
        cmd += ["--debug"]
    cmd += [command] + args_and_opts
    logger.debug("running command: %s", command)
    return run_cmd(cmd, print_output=print_output)


def buildah_with_output(command, args_and_opts, debug=False):
    cmd = ["buildah"]
    if debug:
        cmd += ["--debug"]
    cmd += [command] + args_and_opts
    output = run_cmd(cmd, return_output=True)
    logger.debug("output: %s", output)
    return output


class BuildahBuilder(Builder):
    ansible_connection = "buildah"
    name = "buildah"

    def __init__(self, base_image, target_image, metadata, debug=False):
        super().__init__(base_image, metadata, debug=debug)
        self.target_image = target_image
        # FIXME: pick a container name which does not exist
        self.ansible_host = target_image + "-cont"
        buildah_command_exists()

    def create(self, build_volumes=None):
        """
        :param build_volumes: list of str, bind-mount specification: ["/host:/cont", ...]
        """
        create_buildah_container(
            self.name, self.ansible_host, build_volumes=build_volumes, debug=self.debug)
        # let's apply configuration before execing the playbook, except for user
        configure_buildah_container(
            self.ansible_host, working_dir=self.image_metadata.working_dir,
            env_vars=self.image_metadata.env_vars,
            ports=self.image_metadata.ports,
            labels=self.image_metadata.labels,  # labels are not applied when they are configured
                                                # before doing commit
            debug=self.debug
        )

    def commit(self, image_name):
        if self.image_metadata.user or self.image_metadata.cmd or self.image_metadata.volumes:
            # change user if needed
            configure_buildah_container(
                self.ansible_host, user=self.image_metadata.user,
                cmd=self.image_metadata.cmd,
                volumes=self.image_metadata.volumes,
            )
        buildah("commit", [self.ansible_host, image_name], print_output=True,
                debug=self.debug)

    def clean(self):
        """
        clean working container
        """
        buildah("rm", [self.ansible_host], debug=self.debug)

    def is_image_present(self, image_reference):
        """
        :return: True when the selected image is present, False otherwise
        """
        return bool(get_buildah_image_id(image_reference))

    def pull(self):
        """
        pull base image
        """
        logger.info("pull base image: %s", self.name)
        podman_command_exists()
        pull_buildah_image(self.name)

    def find_python_interpreter(self):
        """
        find python executable in the base image, order:
         * /usr/bin/python3
         * /usr/bin/python2
         * /usr/bin/python

        :return: str, path to python interpreter
        """
        for i in self.python_interpr_prio:
            cmd = ["ls", i]
            try:
                podman_run_cmd(self.name, cmd, log_stderr=False)
            except subprocess.CalledProcessError:
                logger.info("python interpreter %s does not exist", i)
                continue
            else:
                logger.info("using python interpreter %s", i)
                return i
        raise RuntimeError("no python interpreter found in image %s" % self.name)
