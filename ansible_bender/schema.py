"""
Jsonschema for Build and ImageMetadata
"""

# thanks https://www.jsonschema.net/
BUILD_SCHEMA = {
    "definitions": {},
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "2",
    "type": "object",
    "title": "Build Schema",
    "optional": [
        "build_id",
        "build_finished_time",
        "build_start_time",
        "build_volumes",
        "layers",
        "final_layer_id",
        "layer_index",
        "build_container",
        "cache_tasks",
        "log_lines",
        "layering",
        "debug",
        "verbose",
        "pulled",
        "ansible_extra_args",
        "python_interpreter"
    ],
    "required": [
        "playbook_path",
        "metadata",
        "state",
        "base_image",
        "target_image",
        "builder_name",
    ],
    "properties": {
        "build_id": {
            "$id": "#/properties/build_id",
            "type": ["null", "string"],
            "title": "Unique build identifier",
            "default": None,
            "examples": [
                "1", "42", None
            ]
        },
        "playbook_path": {
            "$id": "#/properties/playbook_path",
            "type": "string",
            "title": "Path to playbook",
            "examples": [
                "./playbook.yaml"
            ]
        },
        "build_volumes": {
            "$id": "#/properties/build_volumes",
            "type": "array",
            "title": "List of volumes available during build",
            "items": {
                "$id": "#/properties/build_volumes/items",
                "type": "string",
                "title": "The Items Schema",
                "default": "",
                "examples": [
                    "/c:/d"
                ],
                "pattern": "^(.*)$"
            }
        },
        "metadata": {
            "$id": "#/properties/metadata",
            "type": "object",
            "title": "Image metadata"
        },
        "state": {
            "$id": "#/properties/state",
            "type": "string",
            "title": "Build state",
            "default": "",
            "examples": [
                "new"
            ],
            "pattern": "^(.*)$"
        },
        "build_start_time": {
            "$id": "#/properties/build_start_time",
            "type": ["string", "null"],
            "title": "Time when the build started",
            "examples": [
                ""
            ]
        },
        "build_finished_time": {
            "$id": "#/properties/build_finished_time",
            "type": ["string", "null"],
            "title": "Time when the build finished",
            "examples": [
                ""
            ]
        },
        "base_image": {
            "$id": "#/properties/base_image",
            "type": "string",
            "title": "Base image",
            "examples": [
                "fedora:29"
            ],
            "pattern": "^(.*)$"
        },
        "target_image": {
            "$id": "#/properties/target_image",
            "type": "string",
            "title": "Name of the final image which we build",
            "examples": [
                "my-funky-image"
            ],
            "pattern": "^(.*)$"
        },
        "builder_name": {
            "$id": "#/properties/builder_name",
            "type": ["string", "null"],
            "title": "Builder to use during a build",
            "examples": [
                "buildah"
            ]
        },
        "layers": {
            "$id": "#/properties/layers",
            "type": "array",
            "title": "Layers of the image"
        },
        "final_layer_id": {
            "$id": "#/properties/final_layer_id",
            "type": ["null", "string"],
            "title": "ID of the final layer",
            "examples": [
                "...some hash..."
            ]
        },
        "layer_index": {
            "$id": "#/properties/layer_index",
            "type": "object",
            "title": "index for layers"
        },
        "build_container": {
            "$id": "#/properties/build_container",
            "type": ["string", "null"],
            "title": "Name of the container where the build is happening",
            "examples": [
                "my-image-...-cont"
            ]
        },
        "cache_tasks": {
            "$id": "#/properties/cache_tasks",
            "type": "boolean",
            "title": "Should we cache tasks?",
            "examples": [
                True
            ],
        },
        "log_lines": {
            "$id": "#/properties/log_lines",
            "type": "array",
            "title": "A list of log lines"
        },
        "layering": {
            "$id": "#/properties/layering",
            "type": "boolean",
            "title": "Should we layer after each task?",
            "default": "",
            "examples": [
                False
            ],
        },
        "debug": {
            "$id": "#/properties/debug",
            "type": "boolean",
            "title": "Should we print debug logs?",
            "examples": [
                False
            ]
        },
        "verbose": {
            "$id": "#/properties/verbose",
            "type": "boolean",
            "title": "Should we act verbosely?",
            "examples": [
                True
            ]
        },
        "pulled": {
            "$id": "#/properties/pulled",
            "type": "boolean",
            "title": "Was the base image pulled?",
            "examples": [
                False
            ]
        },
        "ansible_extra_args": {
            "$id": "#/properties/ansible_extra_args",
            "type": ["string", "null"],
            "title": "Extra args to pass to ansible-playbook",
            "examples": [
                "--vv -e key=value"
            ],
            "pattern": "^(.*)$"
        },
        "python_interpreter": {
            "$id": "#/properties/python_interpreter",
            "type": ["string", "null"],
            "title": "Path to python interpreter within the base image",
            "examples": [
                "/usr/bin/python4"
            ]
        }
    }
}

IMAGE_META_SCHENA = {
    "definitions": {},
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "1",
    "type": "object",
    "title": "Image Metadata Schema",
    "optional": [
        "working_dir",
        "labels",
        "annotations",
        "env_vars",
        "cmd",
        "user",
        "ports",
        "volumes"
    ],
    "properties": {
        "working_dir": {
            "$id": "#/properties/working_dir",
            "type": ["string", "null"],
            "title": "Path to a working directory within a container image",
            "default": "",
            "examples": [
                "/workshop"
            ],
            "pattern": "^(.*)$"
        },
        "labels": {
            "$id": "#/properties/labels",
            "type": "object",
            "title": "Key/value data to apply to the final image",
            "additionalProperties": {"type": "string"}
        },
        "annotations": {
            "$id": "#/properties/annotations",
            "type": "object",
            "title": "Key/value data to apply to the final image",
            "additionalProperties": {"type": "string"}
        },
        "env_vars": {
            "$id": "#/properties/env_vars",
            "type": "object",
            "title": "Implicit environment variables to set in a container",
            "additionalProperties": {"type": "string"}
        },
        "cmd": {
            "$id": "#/properties/cmd",
            "type": ["string", "null"],
            "title": "A default command to invoke the container",
            "default": "",
            "examples": [
                "command -x -y z"
            ],
            "pattern": "^(.*)$"
        },
        "user": {
            "$id": "#/properties/user",
            "type": ["string", "null"],
            "title": "UID or username used to invoke the container",
            "default": "",
            "examples": [
                "leonardo"
            ],
            "pattern": "^(.*)$"
        },
        "ports": {
            "$id": "#/properties/ports",
            "type": "array",
            "title": "A list of ports which are meant to be exposed on the host",
            "items": {
                "$id": "#/properties/ports/items",
                "type": "string",
                "title": "The Items Schema",
                "default": "",
                "examples": [
                    "80", "443"
                ],
                "pattern": "^(.*)$"
            }
        },
        "volumes": {
            "$id": "#/properties/volumes",
            "type": "array",
            "title": "A list of paths which are meant to be hosted outside of the container",
            "items": {
                "$id": "#/properties/volumes/items",
                "type": "string",
                "title": "The Items Schema",
                "default": "",
                "examples": [
                    "/path/to/a/directory"
                ],
                "pattern": "^(.*)$"
            }
        }
    }
}