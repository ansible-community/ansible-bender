"""
Base class for builders
"""
from enum import Enum


class BuildState(Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"


class Builder:
    ansible_connection = "default-value"
    name = "default-value"

    def __init__(self, build, debug=False):
        """
        :param build: instance of Build
        :param debug: bool, provide debug output if True
        """
        self.build = build
        self.ansible_host = None
        self.debug = debug
        self.python_interpr_prio = (
            "/usr/bin/python3",
            "/usr/local/bin/python3",
            "/usr/bin/python3.7",
            "/usr/bin/python37",
            "/usr/bin/python3.6",
            "/usr/bin/python36",
            "/usr/bin/python2",
            "/usr/local/bin/python2",
            "/usr/bin/python",
            "/usr/local/bin/python",
        )

    def create(self):
        """
        create a container where all the work happens
        """

    def run(self, image_name, command):
        """
        run provided command in the selected image and return output

        :param image_name: str
        :param command: list of str
        :return: str (output)
        """

    def commit(self, image_name):
        """
        snapshot the artifact and create an image

        :param image_name: str, name the snapshot
        """

    def clean(self):
        """
        clean working container
        """

    def get_image_id(self, image_name):
        """ return image_id for provided image """

    def is_image_present(self, image_reference):
        """
        :return: True when the selected image is present, False otherwise
        """

    def is_base_image_present(self):
        """
        :return: True when the base image is present, False otherwise
        """
        return self.is_image_present(self.build.base_image)

    def pull(self):
        """
        pull base image
        """

    def push(self, build, target, force=False):
        """
        push built image into a remote location

        :param target: str, transport:details
        :param build: instance of Build
        :param force: bool, bypass checks if True
        :return: None
        """

    def find_python_interpreter(self):
        """
        find python executable in the base image, for prio order see constructor

        :return: str, path to python interpreter
        """

    def get_logs(self):
        """
        obtain logs for the selected build

        :return: list of str
        """

    def sanity_check(self):
        """
        invoke container tooling and thus verify they work well
        """

    def check_container_creation(self):
        """
        check that containers can be created
        """
