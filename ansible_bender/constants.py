OUT_LOGGER = "ab-out"
OUT_LOGGER_FORMAT = "%(message)s"
TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S%f"
TIMESTAMP_FORMAT_TOGETHER = "%Y%m%d%H%M%S%f"
NO_CACHE_TAG = "no-cache"

# configuration related constants
ANNOTATIONS_KEY = "annotations"

# ansible playbook template in yaml
PLAYBOOK_TEMPLATE = """---
- name: Containerized version of $project
  hosts: all
  vars:
    a_variable: value
    # configuration specific for ansible-bender
    ansible_bender:
      base_image: fedora:latest
      target_image:
        # command to run by default when invoking the container
        cmd: /command.sh
        name: $project
      working_container:
        volumes:
        # mount this git repo to the working container at /src
        - "{{ playbook_dir }}:/src"
  tasks:
  - name: install dependencies needed to run project $project
    package:
      name:
      - a_package
      - another_package
      state: present
"""
