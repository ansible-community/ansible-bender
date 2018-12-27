#!/bin/bash
set -x
BASE_IMAGE="registry.fedoraproject.org/fedora:29"
# buildah errors to pull, then there are some errors while doing inspect
buildah pull ${BASE_IMAGE}
podman pull ${BASE_IMAGE}
buildah inspect ${BASE_IMAGE}
podman inspect ${BASE_IMAGE}

buildah info
podman info

exec ansible-bender --debug build-inside-openshift
