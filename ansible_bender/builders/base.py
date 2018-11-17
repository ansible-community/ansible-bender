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


class Layer:
    """ This is an image layer """

    def __init__(self, content, layer_id, base_image_id, cached=None):
        """
        :param content: what's the content of the layer
        :param layer_id:
        :param base_image_id:
        :param cached: bool, was it loaded from cache?
        """
        self.content = content
        self.layer_id = layer_id
        self.base_image_id = base_image_id
        self.cached = cached

    def __str__(self):
        return f"layer_id={self.layer_id} cached={self.cached}"

    def __repr__(self):
        return f"Layer(layer_id={self.layer_id}, cached={self.cached}, base={self.base_image_id})"

    def to_dict(self):
        return {
            "content": self.content,
            "layer_id": self.layer_id,
            "base_image_id": self.base_image_id,
            "cached": self.cached
        }

    @classmethod
    def from_json(cls, j):
        return cls(
            j["content"],
            j["layer_id"],
            j["base_image_id"],
            cached=j["cached"]
        )


class Build:
    """ class which represents a build """
    def __init__(self):
        self.build_id = None  # PK, should be set by database
        self.playbook_path = None
        self.build_volumes = []  # volumes for the build container
        self.metadata = None  # Image metadata
        self.state = None  # enum, BuildState
        self.build_start_time = None
        self.build_finished_time = None
        self.base_image = None
        self.build_container = None
        self.target_image = None
        self.builder_name = None
        self.layers = []
        self.final_layer_id = None  # once the image is built, this is the final layer: content + metadata
        self.layer_index = {}  # this is an index for layers: `layer_id: Layer()`
        self.cache_tasks = True  # we cache by default, a user can opt out
        self.log_lines = []  # a list of strings
        self.layering = True
        self.debug = None
        self.verbose = None

    def to_dict(self):
        """ serialize """
        return {
            "build_id": self.build_id,
            "playbook_path": self.playbook_path,
            "build_volumes": self.build_volumes,
            "metadata": self.metadata.to_dict(),
            "state": self.state.value,
            "build_start_time": self.build_start_time.strftime(TIMESTAMP_FORMAT)
                if self.build_start_time else None,
            "build_finished_time": self.build_finished_time.strftime(TIMESTAMP_FORMAT)
                if self.build_finished_time else None,
            "base_image": self.base_image,
            "target_image": self.target_image,
            "builder_name": self.builder_name,
            "layers": [x.to_dict() for x in self.layers],
            "final_layer_id": self.final_layer_id,
            "layer_index": {x.layer_id: x.to_dict() for x in self.layers},
            "build_container": self.build_container,
            "cache_tasks": self.cache_tasks,
            # we could compress/base64 here, let's go for the easier solution first
            "log_lines": self.log_lines,
            "layering": self.layering,
            "debug": self.debug,
            "verbose": self.verbose
        }

    @classmethod
    def from_json(cls, j):
        """ return Build instance from the provided json """
        b = cls()
        b.build_id = j["build_id"]
        b.playbook_path = j["playbook_path"]
        b.build_volumes = j["build_volumes"]
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
        b.layers = [Layer.from_json(x) for x in j["layers"]]
        b.final_layer_id = j.get("final_layer_id", None)
        b.layer_index = {layer_id: Layer.from_json(layer_data)
                         for layer_id, layer_data in j["layer_index"].items()}
        b.build_container = j["build_container"]
        b.cache_tasks = j["cache_tasks"]
        b.log_lines = j["log_lines"]
        b.layering = j["layering"]
        b.debug = j["debug"]
        b.verbose = j["verbose"]
        return b

    def record_layer(self, content, layer_id, base_image_id, cached=None):
        """
        record a new layer for this build

        :param content:
        :param layer_id:
        :param base_image_id:
        :param cached: bool, was it cached?
        """
        layer = Layer(content, layer_id, base_image_id, cached=cached)
        self.layers.append(layer)
        self.layer_index[layer_id] = layer

    def get_top_layer_id(self):
        """
        return id of the top layer, or None
        """
        if self.layers:
            return self.layers[-1].layer_id

    def get_target_image_id(self):
        """
        this is the preferred way of getting ID of the built image

        :return: str
        """
        if self.state not in [BuildState.DONE, BuildState.FAILED]:
            raise RuntimeError(f"Build have not finished yet, it is in state '{self.state.value}'.")
        return self.get_top_layer_id()

    def was_last_layer_cached(self):
        if self.layers:
            return self.layers[-1].cached

    def record_cache_entry(self, image_id):
        self.layer_index[image_id].cached = True

    def stop_layering(self):
        self.layering = False

    def is_layering_on(self):
        return self.layering


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
