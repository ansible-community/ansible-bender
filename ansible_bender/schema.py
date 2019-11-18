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
        "squash",
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
        "squash": {
            "$id": "#/properties/squash",
            "type": "boolean",
            "title": "Should we squash the final image to a single layer?",
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

IMAGE_META_SCHEMA = {
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
        "entrypoint",
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
        "entrypoint": {
            "$id": "#/properties/entrypoint",
            "type": ["string", "null"],
            "title": "An entrypoint script to configure for the container",
            "default": "",
            "examples": [
                "entrypoint.sh"
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
    },
    "additionalProperties": False
}

PLAYBOOK_SCHEMA = {
    "definitions": {},
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "3",
    "type": "object",
    "title": "Playbook Schema",
    "additionalProperties": False,
    "properties": {
        "working_container": {
            "$id": "#/properties/working_container",
            "type": ["object", "null"],
            "title": "settings for the container where the build occurs",
            "additionalProperties": False,
            "properties": {
                "volumes": {
                    "$id": "#/properties/working_container/properties/volumes",
                    "type": "array",
                    "title": "A list of paths which are meant to be hosted outside of the container",
                    "items": {
                        "$id": "#/properties/working_container/properties/volumes/items",
                        "type": "string",
                        "title": "The Items Schema",
                        "examples": [
                            "/path/to/a/directory"
                        ],
                    }
                },
                "user": {
                    "$id": "#/properties/working_container/properties/user",
                    "type": ["string", "null"],
                    "title": "UID or username used to invoke the container",
                    "examples": [
                        "leonardo"
                    ],
                }
            }
        },
        "target_image": {
            "$id": "#/properties/target_image",
            "type": ["object", "null"],
            "title": "metadata of the final image which we built",
            "additionalProperties": False,
            "properties": {
                "name": {
                    "$id": "#/properties/target_image/properties/name",
                    "type": ["string", "null"],
                    "title": "Path to a working directory within a container image",
                },
                "ports": {
                    "$id": "#/properties/target_image/properties/ports",
                    "type": "array",
                    "title": "A list of ports which are meant to be exposed on the host",
                    "default": "",
                    "items": {
                        "$id": "#/properties/target_image/properties/ports/items",
                        "type": "string",
                        "title": "The Items Schema",
                        "examples": [
                            "80", "443"
                        ],
                    }
                },
                "volumes": {
                    "$id": "#/properties/target_image/properties/volumes",
                    "type": "array",
                    "title": "A list of paths which are meant to be hosted outside of the container",
                    "items": {
                        "$id": "#/properties/target_image/properties/volumes/items",
                        "type": "string",
                        "title": "The Items Schema",
                        "examples": [
                            "/path/to/a/directory"
                        ],
                    }
                },
                "working_dir": {
                    "$id": "#/properties/target_image/properties/working_dir",
                    "type": ["string", "null"],
                    "title": "Path to a working directory within a container image",
                    "examples": [
                        "/workshop"
                    ],
                },
                "labels": {
                    "$id": "#/properties/target_image/properties/labels",
                    "type": "object",
                    "title": "Key/value data to apply to the final image",
                    "additionalProperties": {"type": "string"}
                },
                "annotations": {
                    "$id": "#/properties/target_image/properties/annotations",
                    "type": "object",
                    "title": "Key/value data to apply to the final image",
                    "additionalProperties": {"type": "string"}
                },
                "environment": {
                    "$id": "#/properties/target_image/properties/environment",
                    "type": "object",
                    "title": "implicit environment variables to set in a container",
                    "additionalProperties": {"type": "string"}
                },
                "cmd": {
                    "$id": "#/properties/target_image/properties/cmd",
                    "type": ["string", "null"],
                    "title": "A default command to invoke the container",
                    "default": "",
                    "examples": [
                        "command -x -y z"
                    ],
                },
                "entrypoint": {
                    "$id": "#/properties/target_image/properties/entrypoint",
                    "type": ["string", "null"],
                    "title": "An entrypoint script to configure for the container",
                    "examples": [
                        "entrypoint.sh"
                    ],
                },
                "user": {
                    "$id": "#/properties/target_image/properties/user",
                    "type": ["string", "null"],
                    "title": "UID or username used to invoke the container",
                    "examples": [
                        "leonardo"
                    ],
                },
            },
        },
        "base_image": {
            "$id": "#/properties/base_image",
            "type": "string",
            "title": "name of the container image to use as a base",
            "examples": [
                "fedora:29"
            ],
        },
        "cache_tasks": {
            "$id": "#/properties/cache_tasks",
            "type": "boolean",
            "title": "When true, enable caching mechanism"
        },
        "layering": {
            "$id": "#/properties/layering",
            "type": "boolean",
            "title": "When true, snapshot the image after a task is executed",
        },
        "squash": {
            "$id": "#/properties/squash",
            "type": "boolean",
            "title": "When true, squash the final image down to a single layer",
        },
        "verbose_layer_names": {
            "$id": "#/properties/verbose_layer_names",
            "type": "boolean",
            "title": "tag layers with a verbose name if true (image-name + timestamp), defaults to false",
        },
        "ansible_extra_args": {
            "$id": "#/properties/ansible_extra_args",
            "type": "string",
            "title": "provide extra arguments for ansible-playbook run",
        },
        "buildah_from_extra_args": {
            "$id": "#/properties/buildah_from_extra_args",
            "type": "string",
            "title": "provide extra arguments for `buildah from` command"
        },
    },
}
