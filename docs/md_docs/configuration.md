# Configuration

## Target image metadata

With dockerfiles, this is being usually done with instructions such as `LABEL`,
`ENV` or `EXPOSE`. Bender supports two ways of configuring the metadata:

* Setting specific Ansible variables
* CLI options of `ansible-bender build`


### Via ansible vars

Configuration can be done using ansible variables. Variables can be specified in 
the playbook, host_vars or group_vars. If using host or group vars, you also
need to specify the inventory for your ansible project, either through cli
parameter, `--inventory`, or in `ansible.cfg`.

The values are processed before a build starts. The changes to values are not reflected 
during a playbook run. If your playbook has multiple plays, the `ansible_bender` variable is processed only from the first play.

The `ansible_bender` variables can be specified in one of two ways:

1. a top-level Ansible variable `ansible_bender` with all the values nested under it 
1. prepended with `ansible_bender_*`. This is convenient if you want to split your variables across several files.
For example, you have a group of hosts with a common base container. You could specify the base container
in the groups `group_vars` file and the host specific container information in the `host_vars` file.

#### Top level ansible_bender variable

The ansible bender configuration variables can specified under a single variable.
For example,

##### playbook.yml
```
---
- name: Single variable configuration
  hosts: all
  vars:
    ansible_bender:
      base_image: docker.io/python:3-alpine

      working_container:
        volumes:
          - '{{ playbook_dir }}:/src:Z'

      target_image:
        name: a-very-nice-image
        working_dir: /src
        environment:
          FILE_TO_PROCESS: README.md
```

#### Prepended variables

Variables can also be split out amoung different files.

In this example, there are two hosts in the inventory, belonging to a single group.

##### inventory.yml
```yaml
[group1]
host1
host2
```

You can define a common base container in
the `group_vars` file using the `base_image` variable prepended with `ansible_bender_`

##### group_vars/group1
```
ansible_bender_base_image: docker.io/python:3-alpine
```

Next you can define host specific ansible builder variables in the host_vars

##### host_vars/host1
```
ansible_bender_target_image:
  name: host_var_host1
  working_dir: /tmp
  environment:
    FILE_TO_PROCESS: README.md
```

There are three variables that can be prepended:

1. ansible_bender_base_image
1. ansible_bender_target_image
1. ansible_bender_working_container

#### Top-level keys

| Key name                  | type   | description
|---------------------------|--------|---------------------------------------------------------
| `base_image`              | string | name of the container image to use as a base
| `buildah_from_extra_args` | string | extra CLI arguments to pass to buildah from command
| `ansible_extra_args`      | string | extra CLI arguments to pass to ansible-playbook command
| `working_container`       | dict   | settings for the container where the build occurs
| `target_image`            | dict   | metadata of the final image which we built
| `cache_tasks`             | bool   | When true, enable caching mechanism
| `layering`                | bool   | When true, snapshot the image after a task is executed
| `squash`                  | bool   | When true, squash the final image down to a single layer
| `verbose_layer_names`     | bool   | tag layers with a verbose name if true (image-name + timestamp), defaults to false


#### `working_container`

| Key name             | type            | description                                                          |
|----------------------|-----------------|----------------------------------------------------------------------|
| `volumes`            | list of strings | volumes mappings for the working container (`HOST:CONTAINER:PARAMS`) |
| `user`               | string          | UID or username to invoke the container during build (run ansible)   |
| `entrypoint`         | string          | entrypoint script/command used by the working container              | 

#### `target_image`


| Key name             | type            | description                                                          |
|----------------------|-----------------|----------------------------------------------------------------------|
| `name`               | string          | name of the image                                                    |
| `labels`             | dict            | key/value data to apply to the final image                           |
| `annotations`        | dict            | key/value data to apply to the final image (buildah/runc specific)   |
| `environment`        | dict            | implicit environment variables to set in a container                 |
| `cmd`                | string          | a default command to invoke the container                            |
| `entrypoint`         | string          | entrypoint script to configure for the container                     |
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
      buildah_from_extra_args: "--dns 8.8.8.8"
      ansible_extra_args: "-vvv"

      working_container:
        volumes:
          - "{{ playbook_dir }}:/src"
        entrypoint: ls

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
                            [--squash]
                            [--build-volumes [BUILD_VOLUMES [BUILD_VOLUMES ...]]]
                            [--build-user BUILD_USER] [-w WORKDIR]
                            [-l [LABELS [LABELS ...]]]
                            [--annotation [ANNOTATIONS [ANNOTATIONS ...]]]
                            [-e [ENV_VARS [ENV_VARS ...]]] [--cmd CMD]
                            [--entrypoint ENTRYPOINT]
                            [-u USER] [-p [PORTS [PORTS ...]]]
                            [--runtime-volumes [RUNTIME_VOLUMES [RUNTIME_VOLUMES ...]]]
                            [--extra-buildah-from-args EXTRA_BUILDAH_FROM_ARGS]
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
  --squash              squash final image down to a single layer
  --build-volumes [BUILD_VOLUMES [BUILD_VOLUMES ...]]
                        mount selected directory inside the container during
                        build, should be specified as
                        '/host/dir:/container/dir'
  --build-user BUILD_USER
                        the container gets invoked with this user during build
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
  --entrypoint ENTRYPOINT
                        entrypoint script to configure for the container
  -u USER, --user USER  the container gets invoked with this user by default
  -p [PORTS [PORTS ...]], --ports [PORTS [PORTS ...]]
                        ports to expose from container by default
  --runtime-volumes [RUNTIME_VOLUMES [RUNTIME_VOLUMES ...]]
                        path a directory which has data stored outside of the
                        container
  --extra-buildah-from-args EXTRA_BUILDAH_FROM_ARGS
                        arguments passed to buildah from command (be careful!)
  --extra-ansible-args EXTRA_ANSIBLE_ARGS
                        arguments passed to ansible-playbook command (be
                        careful!)
  --python-interpreter PYTHON_INTERPRETER
                        Path to a python interpreter inside the base image

Please use '--' to separate options and arguments.
```

## Ansible

If you want to configure Ansible itself, you can set any environment variable
and ansible-bender will relay them to `ansible-playbook` command, an example:

```
        ANSIBLE_STDOUT_CALLBACK=debug ansible-bender build simple-playbook.yaml
```

Bender creates ansible.cfg on the fly which is then used during an
ansible-playbook run. If you define ``ANSIBLE_CONFIG``, it will likely break the
build process: you've been warned.

## Ansible roles

If you are using roles in your playbook and they are in a non-standard place,
you can utilize `ANSIBLE_ROLES_PATH` environment variable to tell ansible where
your roles lives. Bender does not tamper with environment variables, all are
passed to ansible-playbook.

## Buildah

If you are familiar with podman and buildah, you know that you can
[configure](https://github.com/containers/buildah/blob/master/docs/buildah.md#files)
these tools. Ansible-bender doesn't change this configuration in any way so
it's up to you how you set up buildah and podman. The same applies for running
ansible-bender as root or not: buildah allows you to utilize rootless
containers.

My suggestion is to use the overlay storage backend. Vfs backend is slow and
inefficient.