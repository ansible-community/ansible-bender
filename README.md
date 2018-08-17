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

**Please note that this project is not affiliated with Ansible project. It's just using Ansible to do something magical.**


## Installation

## Usage

## TODO for MVP

* [x] You can build images with buildah
* [ ] You can build images with docker
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
* [ ] important TODO/FIXME resolved from code


## TODO post MVP

* [ ] Explicit layering
* [ ] Explicit caching
* [ ] A fancy name!
* [ ] You can build images with podman (needs Ansible connection plugin for podman)
