"""
Base class for builders
"""


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
