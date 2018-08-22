# ab

This is a proof of concept implementation of a tool which builds container
images using Ansible playbooks. It has a pluggable builder selection — it is up
to you to pick the tool which will be used to construct your container image.
ab relies on [Ansible connection
plugins](https://docs.ansible.com/ansible/2.6/plugins/connection.html) for
that. You may be asking: why not
[ansible-container](https://github.com/ansible/ansible-container)? This tool is
actually heavily inspired by ansible-container: the main distinction is that
ansible-container covers the complete lifecycle of a containerized application
while ab takes care of image builds only.

**Please note that this project is not affiliated with Ansible project. It's
just using Ansible to do something magical.**


**Status**: proof of concept


## Installation

## Usage

Right now, ab has just a single command and that is... `build`:
```
$ ab build -e SOME=VALUE -l some=other-value -- ./tests/functional/data/basic_playbook.yaml docker.io/library/python:3-alpine this-is-my-image

PLAY [all] ***********************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************
ok: [this-is-my-image-cont]

TASK [Run a sample command] ******************************************************************************************************************
changed: [this-is-my-image-cont]

TASK [create a file] *************************************************************************************************************************
changed: [this-is-my-image-cont]

PLAY RECAP ***********************************************************************************************************************************
this-is-my-image-cont      : ok=3    changed=2    unreachable=0    failed=0

Getting image source signatures
Skipping fetch of repeat blob sha256:73046094a9b835e443af1a9d736fcfc11a994107500e474d0abf399499ed280c
Skipping fetch of repeat blob sha256:8b63854c53f36e35be6b38f35ba6c0cb9ccffdf43ca67fcf74ff7a8011a126c4
Skipping fetch of repeat blob sha256:83b96d0bacdae9d29f02d93fb861aa612d0a50a3e6ff838d8ef1ac18d6588a47
Skipping fetch of repeat blob sha256:95d81b13128eaecbeb8526d03456d6bcba587220a3c23bf8c0d35b542667cb8d
Skipping fetch of repeat blob sha256:98801e48f5965cc825524f30acad1485f797241999f66a2234d12cf9a6967f8a
Copying blob sha256:eb20406495adfe66c0e2b6d89a37d4fe2f5fcf3bedf064588ce7b4b87ff33746

 0 B / 434.50 KiB [------------------------------------------------------------]
 434.50 KiB / 434.50 KiB [==================================================] 0s
Copying config sha256:7558393975c749748a292835a4708c583d574a282f9d79be7e6e6cc8b38be8f0

 0 B / 5.11 KiB [--------------------------------------------------------------]
 5.11 KiB / 5.11 KiB [======================================================] 0s
Writing manifest to image destination
Storing signatures
7558393975c749748a292835a4708c583d574a282f9d79be7e6e6cc8b38be8f0
Image 'this-is-my-image' was built successfully \o/
```

The command line is a bit longer. That's because all metadata about our target image are in there:
```
$ ab build                                       \  # this is the command
     -e SOME=VALUE                               \  # -e sets environment variables
     -l some=other-value                         \  # -l sets labels
     --                                          \  # two dashes separate options from arguments
     ./tests/functional/data/basic_playbook.yaml \  # first argument is a path to a playbook
     docker.io/library/python:3-alpine           \  # second one is a base image (and is pulled if it's not present)
     this-is-my-image                            \  # and finally, target image name
```

## TODO for MVP

* [x] You can build images with buildah
* [x] You can set basic metadata:
  * [x] work dir
  * [x] env vars
  * [x] labels
  * [x] user
  * [x] cmd
  * [x] ports
* [x] You can do volume mounts during build
* [ ] README
* [x] Functional tests
* [ ] python packaging
* [x] user experience
  * [x] print ansible output by default
  * [x] tinker default and verbose outputs
* [ ] important TODO/FIXME resolved from code
  * [x] check for presence of binaries


## TODO post MVP

* [ ] Explicit layering
* [ ] Explicit caching
* [ ] A fancy name!
* [ ] You can build images with podman (needs Ansible connection plugin for podman)
* [ ] You can build images with docker (incubator maybe?)
