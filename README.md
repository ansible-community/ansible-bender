# ansible-bender
[![PyPI version](https://badge.fury.io/py/ansible-bender.svg)](https://badge.fury.io/py/ansible-bender)
![GitHub Release Date](https://img.shields.io/github/release-date/ansible-community/ansible-bender?label=Latest%20release)
![PyPI - Status](https://img.shields.io/pypi/status/ansible-bender)
![GitHub](https://img.shields.io/github/license/ansible-community/ansible-bender)
![PyPI - Downloads](https://img.shields.io/pypi/dm/ansible-bender)

This is a tool which bends containers using
[Ansible](https://github.com/ansible/ansible)
[playbooks](https://docs.ansible.com/ansible/latest/user_guide/playbooks.html)
and turns them into container images. It has a pluggable builder selection —
it is up to you to pick the tool which will be used to construct your container
image. Right now the only supported builder is
[buildah](https://github.com/containers/buildah).
[More](http://github.com/ansible-community/ansible-bender/issues/25) [to
come](http://github.com/ansible-community/ansible-bender/issues/26) in the future.
Ansible-bender (ab) relies on [Ansible connection
plugins](https://docs.ansible.com/ansible/2.6/plugins/connection.html) for
performing builds.

tl;dr Ansible is the frontend, buildah is the backend.

The concept is described in following blog posts:
* [Building containers with buildah and ansible](https://blog.tomecek.net/post/building-containers-with-buildah-and-ansible/).
* [Ansible and Podman Can Play Together Now](https://blog.tomecek.net/post/ansible-and-podman-can-play-together-now/).

You may be asking: why not
[ansible-container](https://github.com/ansible/ansible-container)? Ansible bender is
actually heavily inspired by ansible-container: the main distinction is that
ansible-container covers the complete lifecycle of a containerized application
while ab takes care of image builds only.


**Status**: ready to be used

Ansible-bender was recently moved to the ansible-community organization. \o/

## Contents
* [Features](https://github.com/ansible-community/ansible-bender/docs/md_docs/features.md)
* [Interface](https://github.com/ansible-community/ansible-bender/docs/md_docs/interface.md)
* [Installation](https://github.com/ansible-community/ansible-bender/docs/md_docs/installation.md)
* [Configuration](https://github.com/ansible-community/ansible-bender/docs/md_docs/configuration.md)
* [Usage](https://github.com/ansible-community/ansible-bender/docs/md_docs/usage.md)
* [Caching and Layering mechanism](https://github.com/ansible-community/ansible-bender/docs/md_docs/cacheandlayer.md)
* [Contribution guide](https://github.com/ansible-community/ansible-bender/docs/md_docs/contributing.md)


### Ansible-bender in OKD

Recently I started experimenting with running ab inside [OpenShift
origin](https://github.com/openshift/origin) — imagine that you'd be able to
build images in your cluster, using Ansible playbooks as definitions.

Openshift by default runs its pods in a
[restrictive](https://blog.openshift.com/understanding-service-accounts-sccs/)
environment. In the proof of concept I was forced to run ab in a privileged
pod. In the end, the whole test suite is passing in that privileged pod.
