"""
Base class for builders
"""


class ImageMetadata:
    """
    working_dir: str, path to a working directory within container image
    labels: dict with labels
    env_vars: dict with env vars
    cmd: str, command to run by default in the container
    user: str, username or uid; the container gets invoked with this user by default
    ports: list of str, ports to expose from container by default
    volumes: list of str; paths within the container which has data stored outside
             of the container
    """
    def __init__(self):
        self.working_dir = None
        self.labels = {}
        self.env_vars = {}
        self.cmd = None
        self.user = None
        self.ports = []
        self.volumes = []


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

    def is_image_present(self, image_reference):
        """
        :return: True when the selected image is present, False otherwise
        """

    def is_base_image_present(self):
        """
        :return: True when the base image is present, False otherwise
        """
        return self.is_image_present(self.name)

    def pull(self):
        """
        pull base image
        """
