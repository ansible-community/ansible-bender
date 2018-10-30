"""
Base class for builders
"""
import datetime
from enum import Enum

from ansible_bender.constants import TIMESTAMP_FORMAT


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

    def to_dict(self):
        return {
            "working_dir": self.working_dir,
            "labels": self.labels,
            "env_vars": self.env_vars,
            "cmd": self.cmd,
            "user": self.user,
            "ports": self.ports,
            "volumes": self.volumes
        }

    @classmethod
    def from_json(cls, j):
        """ return Metadata instance from the provided json """
        m = cls()
        m.working_dir = j["working_dir"]
        m.labels = j["labels"]
        m.env_vars = j["env_vars"]
        m.cmd = j["cmd"]
        m.user = j["user"]
        m.ports = j["ports"]
        m.volumes = j["volumes"]
        return m


class Build:
    """ class which represents a build """
    def __init__(self):
        # TODO: record every input about build into db
        self.build_id = None  # PK, should be set by database
        self.metadata = None  # Image metadata
        self.state = None  # enum, BuildState
        self.build_start_time = None
        self.build_finished_time = None
        self.base_image = None
        self.base_layer = None  # ideally this one would be picked up from progress
        self.build_container = None
        self.target_image = None
        self.builder_name = None
        self.progress = []  # TODO: refactor into layers & cache
        self.cache_tasks = True
        self.log_lines = []  # a list of strings

    def to_dict(self):
        """ serialize """
        return {
            "build_id": self.build_id,
            "metadata": self.metadata.to_dict(),
            "state": self.state.value,
            "build_start_time": self.build_start_time.strftime(TIMESTAMP_FORMAT)
                if self.build_start_time else None,
            "build_finished_time": self.build_finished_time.strftime(TIMESTAMP_FORMAT)
                if self.build_finished_time else None,
            "base_image": self.base_image,
            "target_image": self.target_image,
            "builder_name": self.builder_name,
            "progress": self.progress,
            "base_layer": self.base_layer,
            "build_container": self.build_container,
            "cache_tasks": self.cache_tasks,
            # we could compress/base64 here, let's go for the easier solution first
            "log_lines": self.log_lines
        }

    @classmethod
    def from_json(cls, j):
        """ return Build instance from the provided json """
        b = cls()
        b.build_id = j["build_id"]
        b.metadata = ImageMetadata.from_json(j["metadata"])
        b.state = BuildState(j["state"])
        b.build_start_time = None
        sta = j["build_start_time"]
        if sta:
            b.build_start_time = datetime.datetime.strptime(sta, TIMESTAMP_FORMAT)
        b.build_finished_time = None
        fin = j["build_finished_time"]
        if fin:
            b.build_finished_time = datetime.datetime.strptime(fin, TIMESTAMP_FORMAT)
        b.base_image = j["base_image"]
        b.target_image = j["target_image"]
        b.builder_name = j["builder_name"]
        b.progress = j["progress"]
        b.base_layer = j["base_layer"]
        b.build_container = j["build_container"]
        b.cache_tasks = j["cache_tasks"]
        b.log_lines = j["log_lines"]
        return b

    def append_progress(self, content, layer_id, base_image_id):
        self.progress.append(
            {"content": content, "base_image_id": base_image_id, "image_id": layer_id}
        )


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
            "/usr/bin/python2",
            "/usr/local/bin/python2",
            "/usr/bin/python",
            "/usr/local/bin/python",
        )

    def create(self, build_volumes=None):
        """
        :param build_volumes: list of str, bind-mount specification: ["/host:/cont", ...]
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