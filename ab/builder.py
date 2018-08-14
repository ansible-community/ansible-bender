"""
Builder interface
"""
import json
import logging
import subprocess


logger = logging.getLogger(__name__)


class Builder:
    ansible_connection = "default-value"

    def __init__(self, name):
        self.name = name
        self.ansible_host = None

    def create(self):
        """
        create an environment where the build would take place

        :return:
        """

    def commit(self):
        """
        snapshot the artifact and create an image
        :return:
        """


def graceful_get(d, *keys):
    """
    recursively obtain value from nested dict

    :param d: dict
    :param keys:
    :return: value or None
    """
    response = d
    for k in keys:
        try:
            response = response[k]
        except (KeyError, AttributeError, TypeError) as ex:
            logger.error("can't obtain %s: %s", k, ex)
    return response


def inspect_resource(resource_id, resource_type):
    try:
        i = subprocess.check_output(["buildah", "inspect", "-t", resource_type, resource_id])
    except subprocess.CalledProcessError:
        logger.info("no such %s %s", resource_type, resource_id)
        return None
    metadata = json.loads(i)
    return metadata


def get_image_id(container_image):
    metadata = inspect_resource(container_image, "image")
    return graceful_get(metadata, "image-id")


def pull_image(container_image):
    subprocess.check_call(["podman", "pull", container_image])
    return get_image_id(container_image)


def create_buildah_container(
        container_image, container_name, working_dir=None, env_vars=None, user=None,
        volumes=None):
    """
    Create new buildah container according to spec.

    :param container_image:
    :param container_name:
    :param working_dir:
    :param env_vars:
    :param user:
    :param volumes: list of str, same as VOLUME in dockerfile, just metadata
    :return:
    """
    args = ["--name", container_name, container_image]
    # will pull the image by default if it's not present in buildah's storage
    buildah("from", args)

    config_args = []
    if working_dir:
        config_args += ["--workingdir", working_dir]
    if env_vars:
        for k, v in env_vars.items():
            config_args += ["-e", "%s=%s" % (k, v)]
    if volumes:
        for v in volumes:
            config_args += ["-v", v]
    if user:
        config_args += ["--user", user]
    if config_args:
        buildah("config", config_args + [container_name])
    return container_name


def buildah(command, args_and_opts):
    # TODO: make sure buildah command is present on system
    command = ["buildah", command] + args_and_opts
    logger.debug("running command: %s", command)
    return subprocess.check_call(command)


def buildah_with_output(command, args_and_opts):
    command = ["buildah", command] + args_and_opts
    logger.debug("running command: %s", command)
    output = subprocess.check_output(command)
    logger.debug("output: %s", output)
    return output


class BuildahBuilder(Builder):
    ansible_connection = "buildah"

    def __init__(self, base_image, target_image):
        super().__init__(base_image)
        self.target_image = target_image
        self.ansible_host = target_image + "-cont"

    def create(self):
        # FIXME: pick a container name which does not exist
        create_buildah_container(self.name, self.ansible_host)

    def commit(self):
        buildah("commit", [self.ansible_host, self.target_image])
