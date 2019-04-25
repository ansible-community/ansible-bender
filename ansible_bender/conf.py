"""
This is a configuration module
"""
import datetime

from ansible_bender.builders.base import BuildState
from ansible_bender.constants import TIMESTAMP_FORMAT, ANNOTATIONS_KEY
from ansible_bender.schema import IMAGE_META_SCHENA, BUILD_SCHEMA
from ansible_bender.utils import graceful_get

import jsonschema


class ImageMetadata:
    """
    working_dir: str,
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
        self.annotations = {}
        self.env_vars = {}
        self.cmd = None
        self.user = None
        self.ports = []
        self.volumes = []

    def to_dict(self):
        return {
            "working_dir": self.working_dir,
            "labels": self.labels,
            ANNOTATIONS_KEY: self.annotations,
            "env_vars": self.env_vars,
            "cmd": self.cmd,
            "user": self.user,
            "ports": self.ports,
            "volumes": self.volumes
        }

    def update_from_configuration(self, data):
        """ update current object with data provided from Ansible vars """
        self.working_dir = data.get("working_dir", None)
        self.labels.update(data.get("labels", {}))
        self.annotations.update(data.get(ANNOTATIONS_KEY, {}))
        self.env_vars.update(data.get("environment", {}))
        self.cmd = data.get("cmd", None)
        self.user = data.get("user", None)
        self.ports += data.get("ports", [])
        self.volumes += data.get("volumes", [])

    @classmethod
    def from_json(cls, j):
        """ return Metadata instance from the provided json """
        m = cls()
        m.working_dir = j["working_dir"]
        m.labels = j["labels"]
        m.annotations = graceful_get(j, ANNOTATIONS_KEY, default={})
        m.env_vars = j["env_vars"]
        m.cmd = j["cmd"]
        m.user = j["user"]
        m.ports = j["ports"]
        m.volumes = j["volumes"]
        return m

    def validate(self):
        jsonschema.validate(self.to_dict(), IMAGE_META_SCHENA)


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
        self.build_user = None
        self.metadata = None  # Image metadata
        self.state = BuildState.NEW
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
        self.debug = False
        self.verbose = False
        self.pulled = False  # was the base image pulled?
        self.ansible_extra_args = None
        self.python_interpreter = None

    def to_dict(self):
        """ serialize """
        return {
            "build_id": self.build_id,
            "playbook_path": self.playbook_path,
            "build_volumes": self.build_volumes,
            "build_user": self.build_user,
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
            "verbose": self.verbose,
            "pulled": self.pulled,
            "ansible_extra_args": self.ansible_extra_args,
            "python_interpreter": self.python_interpreter,
        }

    def update_from_configuration(self, data):
        """ update current object with data provided from Ansible vars """
        self.build_volumes += graceful_get(data, "working_container", "volumes", default=[])
        self.build_user = graceful_get(data, "working_container", "user")
        self.base_image = graceful_get(data, "base_image")
        self.target_image = graceful_get(data, "target_image", "name")
        # self.builder_name = None
        self.cache_tasks = graceful_get(data, "cache_tasks", default=self.cache_tasks)
        self.layering = graceful_get(data, "layering", default=self.layering)
        self.ansible_extra_args = graceful_get(data, "ansible_extra_args")
        # we should probably get this from the official Ansible variable
        # self.python_interpreter = None

    @classmethod
    def from_json(cls, j):
        """ return Build instance from the provided json """
        b = cls()
        b.build_id = j["build_id"]
        b.playbook_path = j.get("playbook_path", None)
        b.build_volumes = j["build_volumes"]
        b.build_user = j["build_user"]
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
        b.pulled = j["pulled"]
        b.ansible_extra_args = j.get("ansible_extra_args", None)
        b.python_interpreter = j.get("python_interpreter", None)
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
        return self.final_layer_id

    def was_last_layer_cached(self):
        if self.layers:
            return self.layers[-1].cached

    def record_cache_entry(self, image_id):
        self.layer_index[image_id].cached = True

    def stop_layering(self):
        self.layering = False

    def is_layering_on(self):
        return self.layering

    def validate(self):
        jsonschema.validate(self.to_dict(), BUILD_SCHEMA)

    def is_failed(self):
        return self.state == BuildState.FAILED
