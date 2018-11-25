TEST_TARGET := ./tests/
KNIFE := knife

build-knife:
	ansible-bender build ./knife.yml registry.fedoraproject.org/fedora:29 $(KNIFE)

check:
	PYTHONPATH=$(CURDIR) pytest-3 -v $(TEST_TARGET)

check-pypi-packaging:
	podman run --rm -ti -v $(CURDIR):/src -w /src $(KNIFE) bash -c '\
		pip3 install . \
		&& ansible-bender --help \
		&& ansible-bender build --help \
		&& pip3 --version ansible-bender \
		&& twine check . \
		'

#FIXME: try outer container to be rootless
#       build tests image
#       run tests as an unpriv user
# TODO: podman inside needs to use vfs storage driver
check-smoke:
	sudo podman run --net=host --rm -ti -v $(CURDIR):/src -w /src registry.fedoraproject.org/fedora:29 bash -c '\
		dnf install -y buildah podman \
		&& podman pull docker.io/library/python:3-alpine \
		&& pip3 install . \
		&& ansible-bender build ./tests/data/basic_playbook.yaml docker.io/library/python:3-alpine test'
