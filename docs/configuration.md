# Configuration

## Target image metadata

With dockerfiles, this is being usually done with instructions such as `LABEL`,
`ENV` or `EXPOSE`. Bender supports two ways of configuring the metadata:

* Setting specific Ansible variables inside your playbook.
* CLI options of `ansible-bender build`.


### Via playbook vars

Configuration is done using a top-level Ansible variable `ansible_bender`. All
the values are nested under it. The values are processed before a build starts.
The changes to values are not reflected during a playbook run.

If your playbook has multiple plays, the `ansible_bender` variable is processed
only from the first play. All the plays will end up in a single container image.


#### Top-level keys

| Key name             | type   | description                                             |
|----------------------|--------|---------------------------------------------------------|
| `base_image`         | string | name of the container image to use as a base            |
| `ansible_extra_args` | string | extra CLI arguments to pass to ansible-playbook command |
| `working_container`  | dict   | settings for the container where the build occurs       |
| `target_image`       | dict   | metadata of the final image which we built              |
| `cache_tasks`        | bool   | When true, enable caching mechanism                     |
| `layering`           | bool   | When true, snapshot the image after a task is executed  |


#### `working_container`

| Key name             | type            | description                                                          |
|----------------------|-----------------|----------------------------------------------------------------------|
| `volumes`            | list of strings | volumes mappings for the working container (`HOST:CONTAINER:PARAMS`) |
| `user`               | string          | UID or username to invoke the container during build (run ansible)   |

#### `target_image`


| Key name             | type            | description                                                          |
|----------------------|-----------------|----------------------------------------------------------------------|
| `name`               | string          | name of the image                                                    |
| `labels`             | dict            | key/value data to apply to the final image                           |
| `annotations`        | dict            | key/value data to apply to the final image (buildah/runc specific)   |
| `environment`        | dict            | implicit environment variables to set in a container                 |
| `cmd`                | string          | a default command to invoke the container                            |
| `user`               | string          | UID or username used to invoke the container                         |
| `ports`              | list of strings | a list of ports which are meant to be exposed on the host            |
| `volumes`            | list of strings | a list of paths which are meant to be hosted outside of the container|
| `working_dir`        | string          | path to a working directory within a container image                 |


Example of a playbook with variables:

```
- hosts: all
  vars:
    ansible_bender:
      base_image: "docker.io/library/python:3-alpine"
      ansible_extra_args: "-vvv"

      working_container:
        volumes:
          - "{{ playbook_dir }}:/src"

      target_image:
        name: challet
        labels:
          x: y
        environment:
          asd: '{{ playbook_dir }}'
```

Before bender processes the variables, it runs a no-op playbook so that Ansible
expand them. Therefore you can utilize some of the Ansible's native variables.
Please bear in mind that most of the facts won't be available.


### Via CLI

Please check out `ansible-bender build --help` for up to date options:

```
$ ansible-bender build -h
usage: ansible-bender build [-h] [--builder {docker,buildah}] [--no-cache]
                            [--build-volumes [BUILD_VOLUMES [BUILD_VOLUMES ...]]]
                            [-w WORKDIR] [-l [LABELS [LABELS ...]]]
                            [--annotation [ANNOTATIONS [ANNOTATIONS ...]]]
                            [-e [ENV_VARS [ENV_VARS ...]]] [--cmd CMD]
                            [-u USER] [-p [PORTS [PORTS ...]]]
                            [--runtime-volumes [RUNTIME_VOLUMES [RUNTIME_VOLUMES ...]]]
                            [--extra-ansible-args EXTRA_ANSIBLE_ARGS]
                            [--python-interpreter PYTHON_INTERPRETER]
                            PLAYBOOK_PATH [BASE_IMAGE] [TARGET_IMAGE]

positional arguments:
  PLAYBOOK_PATH         path to Ansible playbook
  BASE_IMAGE            name of a container image to use as a base
  TARGET_IMAGE          name of the built container image

optional arguments:
  -h, --help            show this help message and exit
  --builder {docker,buildah}
                        pick preferred builder backend
  --no-cache            disable caching mechanism: storing layers and loading
                        them if a task is unchanged; this option also implies
                        the final image is composed of a base image and one
                        additional layer
  --build-volumes [BUILD_VOLUMES [BUILD_VOLUMES ...]]
                        mount selected directory inside the container during
                        build, should be specified as
                        '/host/dir:/container/dir'
  --build-user USER     the container gets invoked with this user during build
  -w WORKDIR, --workdir WORKDIR
                        path to an implicit working directory in the container
  -l [LABELS [LABELS ...]], --label [LABELS [LABELS ...]]
                        add a label to the metadata of the image, should be
                        specified as 'key=value'
  --annotation [ANNOTATIONS [ANNOTATIONS ...]]
                        Add key=value annotation for the target image
  -e [ENV_VARS [ENV_VARS ...]], --env-vars [ENV_VARS [ENV_VARS ...]]
                        add an environment variable to the metadata of the
                        image, should be specified as 'KEY=VALUE'
  --cmd CMD             command to run by default in the container
  -u USER, --user USER  the container gets invoked with this user by default
  -p [PORTS [PORTS ...]], --ports [PORTS [PORTS ...]]
                        ports to expose from container by default
  --runtime-volumes [RUNTIME_VOLUMES [RUNTIME_VOLUMES ...]]
                        path a directory which has data stored outside of the
                        container
  --extra-ansible-args EXTRA_ANSIBLE_ARGS
                        arguments passed to ansible-playbook command (be
                        careful!)
  --python-interpreter PYTHON_INTERPRETER
                        Path to a python interpreter inside the base image

Please use '--' to separate options and arguments.
```
