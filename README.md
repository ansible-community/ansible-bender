# ansible-bender
[![PyPI version](https://badge.fury.io/py/ansible-bender.svg)](https://badge.fury.io/py/ansible-bender)
![GitHub Release Date](https://img.shields.io/github/release-date/ansible-community/ansible-bender?label=Latest%20release)
![PyPI - Status](https://img.shields.io/pypi/status/ansible-bender)
![GitHub](https://img.shields.io/github/license/ansible-community/ansible-bender)
![PyPI - Downloads](https://img.shields.io/pypi/dm/ansible-bender)

This tool bends containers using
[Ansible](https://github.com/ansible/ansible)
[playbooks](https://docs.ansible.com/ansible/latest/user_guide/playbooks.html)
and turns them into container images. It has a pluggable builder selection —
it is up to you to pick the tool which will be used to construct your container
image. Right now the only supported builder is
[buildah](https://github.com/containers/buildah).
[More](http://github.com/ansible-community/ansible-bender/issues/25) [to
come](http://github.com/ansible-community/ansible-bender/issues/26) in the future.
Ansible-bender (ab) relies on [Ansible connection
plugins](https://docs.ansible.com/ansible/latest/plugins/connection.html) for
performing builds.

tl;dr Ansible is the frontend, buildah is the backend.

The concept is described in following blog posts:
* [Building containers with buildah and ansible](https://blog.tomecek.net/post/building-containers-with-buildah-and-ansible/).
* [Ansible and Podman Can Play Together Now](https://blog.tomecek.net/post/ansible-and-podman-can-play-together-now/).


## Looking for maintainers ❤

[This project doesn't have an active maintainer right now that](https://github.com/ansible-community/ansible-bender/issues/282) would watch issues daily.

If you are a user of ansible-bender and are familiar with Python, please consider becoming a maintainer.


## Features

* You can build your container images with buildah as a backend.
* Ansible playbook is your build recipe.
* You are able to set various image metadata via CLI or as specific Ansible vars:
  * working directory
  * environment variables
  * labels
  * user
  * default command
  * exposed ports
* You can do volume mounts during build.
* Caching mechanism:
  * Every task result is cached as a container image layer.
  * You can turn this off with `--no-cache`.
  * You can disable caching from a certain point by adding a tag `no-cache` to a task.
* You can stop creating new image layers by adding tag `stop-layering` to a task.
* If an image build fails, it's committed and named with a suffix `-[TIMESTAMP]-failed` (so
  you can take a look inside and resolve the issue).
* The tool tries to find python interpreter inside the base image.
* You can push images you built to remote locations such as:
  * a registry, a tarball, docker daemon, ...
  * [podman push](https://github.com/containers/podman/blob/main/docs/source/markdown/podman-push.1.md) is used to perform the push.


## Documentation

You can read more about this project in the documentation:
* [Documentation home](https://ansible-community.github.io/ansible-bender/build/html/index.html)
* [Interface](https://ansible-community.github.io/ansible-bender/build/html/interface.html)
* [Installation](https://ansible-community.github.io/ansible-bender/build/html/installation.html)
* [Configuration](https://ansible-community.github.io/ansible-bender/build/html/configuration.html)
* [Usage](https://ansible-community.github.io/ansible-bender/build/html/usage.html)
* [Caching and Layering mechanism](https://ansible-community.github.io/ansible-bender/build/html/cacheandlayer.html)
* [Contribution guide](https://ansible-community.github.io/ansible-bender/build/html/contributing.html)
* [Ansible-bender in OKD](https://ansible-community.github.io/ansible-bender/build/html/okd.html)
