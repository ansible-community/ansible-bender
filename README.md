# ab

This is a proof of concept implementation of a tool which builds container
images using Ansible playbooks. It has a pluggable builder selection — it is up
to you to pick the tool which will be used to construct your container image.
ab relies on [Ansible connection
plugins](https://docs.ansible.com/ansible/2.6/plugins/connection.html) for
that.

You may be asking: why not
[ansible-container](https://github.com/ansible/ansible-container)? This tool is
actually heavily inspired by ansible-container: the main distinction is that
ansible-container covers the complete lifecycle of a containerized application
while ab takes care of image builds only.

**Please note that this project is not affiliated with Ansible project. It's
just using Ansible to do something magical.**


**Status**: proof of concept


## Features:

* You can build your container images with buildah as a backend.
* Ansible playbook is your build recipe.
* You are able to set various image metadata via CLI:
  * working directory
  * environment variables
  * labels
  * user
  * default command
  * exposed ports
* You can do volume mounts during build.



## Installation

At the moment `ab` is not on PyPI because there is already such project. Hence
I am looking for [a new, catchy name](https://github.com/TomasTomecek/ab/issues/2)!

You can install ab directly from github:
```
$ pip3 install --user https://github.com/TomasTomecek/ab@0.1.0
```

Oh right, and ab is tested only with python 3.


## Usage

**Please note that buildah requires root privileges so you need to invoke ab as root.**

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

Here is a proof that the image is in there:
```
$ podman images this-is-my-image
REPOSITORY                   TAG      IMAGE ID       CREATED        SIZE
localhost/this-is-my-image   latest   7558393975c7   1 minute ago   84.4MB
```


## TODO past 0.1.0

* [ ] Explicit layering
* [ ] Explicit caching
* [ ] A fancy name!
* [ ] You can build images with podman (needs Ansible connection plugin for podman)
* [ ] You can build images with docker (incubator maybe?)
