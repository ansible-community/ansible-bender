# ab

This is a proof of concept implementation of a tool which builds container
images using Ansible playbooks. It has a pluggable builder selection — it is up
to pick the tool which will be used to construct your container image. ab
relies on [Ansible connection
plugins](https://docs.ansible.com/ansible/2.6/plugins/connection.html) here.
You may be asking: why not [ansible-container](https://github.com/ansible/ansible-container)? This tool is heavily inspired
by ansible-container tool: the main distinction is that ansible-container
covers the complete lifecycle of a containerized application while ab takes
care only about image builds.

** Please note that this project is not affiliated with Ansible project. It's just using Ansible to do something magical. **


## Installation

## Usage

## TODO for MVP

* [x] You can build images with buildah
* [ ] You can build images with docker
* [ ] You can set basic metadata: env vars, labels, user, cmd
* [ ] You can do volume mounts during build
* [ ] README
* [x] Functional tests


## TODO post MVP

* [ ] Explicit layering
* [ ] Explicit caching
