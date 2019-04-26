import json
import logging
import subprocess

from ansible_bender.builders.base import Builder
from ansible_bender.utils import graceful_get, run_cmd, buildah_command_exists, \
    podman_command_exists

logger = logging.getLogger(__name__)


def inspect_resource(resource_type, resource_id):
    try:
        i = run_cmd(["buildah", "inspect", "-t", resource_type, resource_id],
                    return_output=True, log_output=False)
    except subprocess.CalledProcessError:
        logger.info("no such %s %s", resource_type, resource_id)
        return None
    try:
        metadata = json.loads(i)
    except IndexError:
        logger.info("no such %s %s", resource_type, resource_id)
        return None
    return metadata


def get_buildah_image_id(container_image):
    metadata = inspect_resource("image", container_image)
    return graceful_get(metadata, "FromImageID")


def pull_buildah_image(container_image):
    run_cmd(["buildah", "pull", container_image],
            save_output_in_exc=False,
            log_stderr=False, print_output=True, log_output=False)


def does_image_exist(container_image):
    # cmd = ["podman", "image", "exists", container_image]
    # https://github.com/containers/libpod/issues/2924
    # https://github.com/ansible-community/ansible-bender/issues/114
    cmd = ["buildah", "inspect", "-t", "image", container_image]
    run_cmd(cmd, print_output=True)


def podman_run_cmd(container_image, cmd, log_stderr=True, return_output=False):
    """
    run provided command in selected container image using podman; raise exc when command fails

    :param container_image: str
    :param cmd: list of str
    :param log_stderr: bool, log errors to stdout as ERROR level
    :param return_output: bool, if True, return output of the command
    :return: stdout output
    """
    return run_cmd(["podman", "run", "--rm", container_image] + cmd,
                   return_output=return_output, log_stderr=log_stderr)


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
        for volume in build_volumes:
            args += ["-v", volume]
    args += ["--name", container_name, container_image]
    # will pull the image by default if it's not present in buildah's storage
    buildah("from", args, debug=debug, log_stderr=True)


def configure_buildah_container(container_name, working_dir=None, env_vars=None,
                                labels=None, annotations=None,
                                user=None, cmd=None, ports=None, volumes=None,
                                debug=False):
    """
    apply metadata on the container so they get inherited in an image

    :param container_name: name of the container to work in
    :param working_dir: str, path to a working directory within container image
    :param labels: dict with labels
    :param annotations: dict with annotations
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
    if annotations:
        for k, v in annotations.items():
            config_args += ["--annotation", "%s=%s" % (k, v)]
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


def buildah(command, args_and_opts, print_output=False, debug=False, log_stderr=False):
    cmd = ["buildah"]
    # if debug:
    #     cmd += ["--debug"]
    cmd += [command] + args_and_opts
    logger.debug("running command: %s", command)
    return run_cmd(cmd, print_output=print_output, log_stderr=log_stderr)


def buildah_with_output(command, args_and_opts, debug=False):
    cmd = ["buildah"]
    # if debug:
    #     cmd += ["--debug"]
    cmd += [command] + args_and_opts
    output = run_cmd(cmd, return_output=True)
    logger.debug("output: %s", output)
    return output


class BuildahBuilder(Builder):
    ansible_connection = "buildah"
    name = "buildah"

    def __init__(self, build, debug=False):
        """
        :param build: instance of Build
        :param debug: bool, run buildah in debug or not?
        """
        super().__init__(build, debug=debug)
        self.target_image = build.target_image
        self.ansible_host = build.build_container
        self.logs = []
        buildah_command_exists()
        podman_command_exists()

    def create(self):
        """
        create a container where all the work happens
        """
        create_buildah_container(
            self.build.get_top_layer_id(), self.ansible_host,
            build_volumes=self.build.build_volumes, debug=self.debug)
        # let's apply configuration before execing the playbook, except for user
        configure_buildah_container(
            self.ansible_host, working_dir=self.build.metadata.working_dir,
            user=self.build.build_user,
            env_vars=self.build.metadata.env_vars,
            ports=self.build.metadata.ports,
            labels=self.build.metadata.labels,  # labels are not applied when they are configured
                                                # before doing commit
            annotations=self.build.metadata.annotations,
            debug=self.debug
        )

    def run(self, image_name, command):
        """
        run provided command in the selected image and return output

        :param image_name: str
        :param command: list of str
        :return: str (output)
        """
        cmd = ["podman", "run", "--rm", image_name] + command
        return run_cmd(cmd, return_output=True)

    def swap_working_container(self):
        """
        remove current working container and replace it with the provided one
        """
        self.clean()
        self.create()

    def commit(self, image_name, print_output=True, final_image=False):
        if final_image:
            user=self.build.metadata.user
        else:
            user=self.build.build_user

        if self.build.metadata.user or self.build.metadata.cmd or self.build.metadata.volumes:
            # change user if needed
            configure_buildah_container(
                self.ansible_host, user=user,
                cmd=self.build.metadata.cmd,
                volumes=self.build.metadata.volumes,
            )
        buildah("commit", [self.ansible_host, image_name], print_output=print_output,
                debug=self.debug)
        return self.get_image_id(image_name)

    def clean(self):
        """
        clean working container
        """
        buildah("rm", [self.ansible_host], debug=self.debug)

    def get_image_id(self, image_name):
        """ return image_id for provided image """
        image_id = get_buildah_image_id(image_name)
        if not image_id:
            raise RuntimeError("We haven't got any image ID: the image is not present "
                               "or buildah/podman is malfunctioning.")
        return image_id

    def is_image_present(self, image_reference):
        """
        :return: True when the selected image is present, False otherwise
        """
        if not image_reference:
            return False
        try:
            does_image_exist(image_reference)
        except subprocess.CalledProcessError:
            return False
        else:
            return True

    def pull(self):
        """
        pull base image
        """
        logger.info("pulling base image: %s", self.build.base_image)
        pull_buildah_image(self.build.base_image)

    def push(self, build, target, force=False):
        """
        push built image into a remote location using `podman push`

        :param target: str, transport:details
        :param build: instance of Build
        :param force: bool, bypass checks if True
        :return: None
        """
        built_image = build.get_target_image_id()
        cmd = ["buildah", "push", built_image, target]
        # podman prints progress to stderr
        run_cmd(cmd, print_output=False, log_stderr=False)

    def find_python_interpreter(self):
        """
        find python executable in the base image

        :return: str, path to python interpreter
        """
        for i in self.python_interpr_prio:
            cmd = ["ls", i]
            try:
                run_cmd(["podman", "run", "--rm", self.build.base_image] + cmd,
                        log_stderr=False, log_output=True)
            except subprocess.CalledProcessError:
                logger.info("python interpreter %s does not exist", i)
                continue
            else:
                logger.info("using python interpreter %s", i)
                return i
        logger.error("couldn't locate python interpreter, tried these paths: %s", self.python_interpr_prio)
        raise RuntimeError(f"no python interpreter was found in the base image \"{self.build.base_image}\""
                           ", you can specify the path via CLI option --python-interpreter")

    def get_logs(self):
        """
        obtain logs for the selected build

        :return: list of str
        """

    def sanity_check(self):
        """
        invoke container tooling and thus verify they work well
        """
        # doing podman info would be super-handy, but it will immensely clutter the output
        logger.debug("checking that podman command works")
        run_cmd(["podman", "version"], log_stderr=True, log_output=True)
        logger.debug("checking that buildah command works")
        run_cmd(["buildah", "version"], log_stderr=True, log_output=True)

    def check_container_creation(self):
        """
        check that containers can be created
        """
        logger.debug("trying to create a dummy container using podman")
        podman_run_cmd(self.build.base_image, ["true"], log_stderr=True)
