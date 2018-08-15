"""
Builder interface
"""
import json
import logging
import subprocess


logger = logging.getLogger(__name__)


class ImageMetadata:
    def __init__(self):
        self.env_vars = {}
        self.labels = {}
        self.user = None
        self.command = []


class Builder:
    ansible_connection = "default-value"
    name = "default-value"

    def __init__(self, name, metadata):
        """
        :param name: name of the base image
        :param metadata: instance of ImageMetadata
        """
        self.name = name
        self.ansible_host = None
        self.image_metadata = metadata

    def create(self, build_volumes=None):
        """
        :param build_volumes: list of str, bind-mount specification: ["/host:/cont", ...]
        """

    def commit(self):
        """
        snapshot the artifact and create an image
        """

    def clean(self):
        """
        clean working container
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


def inspect_buildah_resource(resource_type, resource_id):
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


def create_buildah_container(container_image, container_name, build_volumes=None):
    """
    Create new buildah container according to spec.

    :param container_image: name of the image
    :param container_name: name of the container to work in
    :param build_volumes: list of str, bind-mount specification: ["/host:/cont", ...]
    """
    args = []
    if build_volumes:
        args += ["-v"] + build_volumes
    args += ["--name", container_name, container_image]
    # will pull the image by default if it's not present in buildah's storage
    buildah("from", args)


def configure_buildah_container(container_name, working_dir=None, env_vars=None,
                                labels=None, user=None, volumes=None):
    """
    apply metadata on the container so they get inherited in an image

    :param container_name: name of the container to work in
    :param working_dir:
    :param labels: dict with labels
    :param env_vars: dict with env vars
    :param user:
    :param volumes:
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
    name = "buildah"

    def __init__(self, base_image, target_image, metadata):
        super().__init__(base_image, metadata)
        self.target_image = target_image
        self.ansible_host = target_image + "-cont"

    def create(self, build_volumes=None):
        """
        :param build_volumes: list of str, bind-mount specification: ["/host:/cont", ...]
        """
        # FIXME: pick a container name which does not exist
        # TODO: pull image if not present
        create_buildah_container(self.name, self.ansible_host, build_volumes=build_volumes)
        # let's apply configuration before execing the playbook
        configure_buildah_container(
            self.ansible_host, working_dir=None, env_vars=self.image_metadata.env_vars,
            labels=self.image_metadata.labels, user=self.image_metadata.user
        )

    def commit(self):
        buildah("commit", [self.ansible_host, self.target_image])

    def clean(self):
        """
        clean working container
        """
        buildah("rm", [self.ansible_host])


BUILDERS = {
    BuildahBuilder.name: BuildahBuilder
}


def get_builder(builder_name):
    try:
        return BUILDERS[builder_name]
    except KeyError:
        raise RuntimeError("No such builder %s", builder_name)
