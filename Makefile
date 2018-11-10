TEST_TARGET := ./tests/

check:
	PYTHONPATH=$(CURDIR) pytest-3 -v $(TEST_TARGET)

check-pypi-packaging:
	podman run --rm -ti -v $(CURDIR):/src -w /src registry.fedoraproject.org/fedora:29 bash -c '\
		pip3 install . \
		&& ab --help \
		&& ab build --help'

#FIXME: try outer container to be rootless
#       build tests image
#       run tests as an unpriv user
check-smoke:
	sudo podman run --rm -ti -v $(CURDIR):/src -w /src registry.fedoraproject.org/fedora:29 bash -c '\
		dnf install -y buildah podman \
		&& podman pull docker.io/library/python:3-alpine \
		&& pip3 install . \
		&& ab build ./tests/data/basic_playbook.yaml docker.io/library/python:3-alpine test'
