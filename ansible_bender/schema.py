"""
Jsonschema for Build and ImageMetadata
"""

# thanks https://www.jsonschema.net/
BUILD_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
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
            "type": ["null", "string"],
            "title": "Unique build identifier",
            "examples": [
                "1", "42", None
            ]
        },
        "playbook_path": {
            "type": "string",
            "title": "Path to playbook",
            "examples": [
                "./playbook.yaml"
            ]
        },
        "build_volumes": {
            "type": "array",
            "title": "List of volumes available during build",
            "items": {
                "type": "string",
                "examples": [
                    "/c:/d"
                ],
            }
        },
        "metadata": {
            "type": "object",
            "title": "Image metadata"
        },
        "state": {
            "type": "string",
            "title": "Build state",
            "examples": [
                "new"
            ],
        },
        "build_start_time": {
            "type": ["string", "null"],
            "title": "Time when the build started",
            "examples": [
                ""
            ]
        },
        "build_finished_time": {
            "type": ["string", "null"],
            "title": "Time when the build finished",
            "examples": [
                ""
            ]
        },
        "base_image": {
            "type": "string",
            "title": "Base image",
            "examples": [
                "fedora:29"
            ],
        },
        "target_image": {
            "type": "string",
            "title": "Name of the final image which we build",
            "examples": [
                "my-funky-image"
            ],
        },
        "builder_name": {
            "type": ["string", "null"],
            "title": "Builder to use during a build",
            "examples": [
                "buildah"
            ]
        },
        "layers": {
            "type": "array",
            "title": "Layers of the image"
        },
        "final_layer_id": {
            "type": ["null", "string"],
            "title": "ID of the final layer",
            "examples": [
                "...some hash..."
            ]
        },
        "layer_index": {
            "type": "object",
            "title": "index for layers"
        },
        "build_container": {
            "type": ["string", "null"],
            "title": "Name of the container where the build is happening",
            "examples": [
                "my-image-...-cont"
            ]
        },
        "cache_tasks": {
            "type": "boolean",
            "title": "Should we cache tasks?",
            "examples": [
                True
            ],
        },
        "log_lines": {
            "type": "array",
            "title": "A list of log lines"
        },
        "layering": {
            "type": "boolean",
            "title": "Should we layer after each task?",
            "examples": [
                False
            ],
        },
        "squash": {
            "type": "boolean",
            "title": "Should we squash the final image to a single layer?",
            "examples": [
                False
            ],
        },
        "debug": {
            "type": "boolean",
            "title": "Should we print debug logs?",
            "examples": [
                False
            ]
        },
        "verbose": {
            "type": "boolean",
            "title": "Should we act verbosely?",
            "examples": [
                True
            ]
        },
        "pulled": {
            "type": "boolean",
            "title": "Was the base image pulled?",
            "examples": [
                False
            ]
        },
        "ansible_extra_args": {
            "type": ["string", "null"],
            "title": "Extra args to pass to ansible-playbook",
            "examples": [
                "--vv -e key=value"
            ],
        },
        "python_interpreter": {
            "type": ["string", "null"],
            "title": "Path to python interpreter within the base image",
            "examples": [
                "/usr/bin/python4"
            ]
        }
    }
}

IMAGE_META_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
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
            "type": ["string", "null"],
            "title": "Path to a working directory within a container image",
            "examples": [
                "/workshop"
            ],
        },
        "labels": {
            "type": "object",
            "title": "Key/value data to apply to the final image",
            "additionalProperties": {"type": "string"}
        },
        "annotations": {
            "type": "object",
            "title": "Key/value data to apply to the final image",
            "additionalProperties": {"type": "string"}
        },
        "env_vars": {
            "type": "object",
            "title": "Implicit environment variables to set in a container",
            "additionalProperties": {"type": "string"}
        },
        "cmd": {
            "type": ["string", "null"],
            "title": "A default command to invoke the container",
            "default": "",
            "examples": [
                "command -x -y z"
            ],
        },
        "entrypoint": {
            "type": ["string", "null"],
            "title": "An entrypoint script to configure for the container",
            "examples": [
                "entrypoint.sh"
            ],
        },
        "user": {
            "$id": "#/properties/user",
            "type": ["string", "null"],
            "title": "UID or username used to invoke the container",
            "examples": [
                "leonardo"
            ],
        },
        "ports": {
            "type": "array",
            "title": "A list of ports which are meant to be exposed on the host",
            "items": {
                "type": "string",
                "examples": [
                    "80", "443"
                ],
            }
        },
        "volumes": {
            "type": "array",
            "title": "A list of paths which are meant to be hosted outside of the container",
            "items": {
                "type": "string",
                "examples": [
                    "/path/to/a/directory"
                ],
            }
        }
    },
    "additionalProperties": False
}

PLAYBOOK_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "Playbook Schema",
    "additionalProperties": False,
    "properties": {
        "working_container": {
            "type": ["object", "null"],
            "title": "settings for the container where the build occurs",
            "additionalProperties": False,
            "properties": {
                "volumes": {
                    "type": "array",
                    "title": "A list of paths which are meant to be hosted outside of the container",
                    "items": {
                        "type": "string",
                        "examples": [
                            "/path/to/a/directory"
                        ],
                    }
                },
                "user": {
                    "type": ["string", "null"],
                    "title": "UID or username used to invoke the container",
                    "examples": [
                        "leonardo"
                    ],
                }
            }
        },
        "target_image": {
            "type": ["object", "null"],
            "title": "metadata of the final image which we built",
            "additionalProperties": False,
            "properties": {
                "name": {
                    "type": ["string", "null"],
                    "title": "Path to a working directory within a container image",
                },
                "ports": {
                    "type": "array",
                    "title": "A list of ports which are meant to be exposed on the host",
                    "items": {
                        "type": "string",
                        "examples": [
                            "80", "443"
                        ],
                    }
                },
                "volumes": {
                    "type": "array",
                    "title": "A list of paths which are meant to be hosted outside of the container",
                    "items": {
                        "type": "string",
                        "examples": [
                            "/path/to/a/directory"
                        ],
                    }
                },
                "working_dir": {
                    "type": ["string", "null"],
                    "title": "Path to a working directory within a container image",
                    "examples": [
                        "/workshop"
                    ],
                },
                "labels": {
                    "type": "object",
                    "title": "Key/value data to apply to the final image",
                    "additionalProperties": {"type": "string"}
                },
                "annotations": {
                    "type": "object",
                    "title": "Key/value data to apply to the final image",
                    "additionalProperties": {"type": "string"}
                },
                "environment": {
                    "type": "object",
                    "title": "implicit environment variables to set in a container",
                    "additionalProperties": {"type": "string"}
                },
                "cmd": {
                    "type": ["string", "null"],
                    "title": "A default command to invoke the container",
                    "examples": [
                        "command -x -y z"
                    ],
                },
                "entrypoint": {
                    "type": ["string", "null"],
                    "title": "An entrypoint script to configure for the container",
                    "examples": [
                        "entrypoint.sh"
                    ],
                },
                "user": {
                    "type": ["string", "null"],
                    "title": "UID or username used to invoke the container",
                    "examples": [
                        "leonardo"
                    ],
                },
            },
        },
        "base_image": {
            "type": "string",
            "title": "name of the container image to use as a base",
            "examples": [
                "fedora:29"
            ],
        },
        "cache_tasks": {
            "type": "boolean",
            "title": "When true, enable caching mechanism"
        },
        "layering": {
            "type": "boolean",
            "title": "When true, snapshot the image after a task is executed",
        },
        "squash": {
            "type": "boolean",
            "title": "When true, squash the final image down to a single layer",
        },
        "verbose_layer_names": {
            "type": "boolean",
            "title": "tag layers with a verbose name if true (image-name + timestamp), defaults to false",
        },
        "ansible_extra_args": {
            "type": "string",
            "title": "provide extra arguments for ansible-playbook run",
        },
        "buildah_from_extra_args": {
            "type": "string",
            "title": "provide extra arguments for `buildah from` command"
        },
    },
}
