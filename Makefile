TEST_TARGET := ./tests/
BASE_IMAGE := registry.fedoraproject.org/fedora:29
PY_PACKAGE := ansible-bender
# container image with ab inside
CONT_IMG := $(PY_PACKAGE)

build-ab-img: recipe.yml
	ansible-bender build --build-volumes $(CURDIR):/src:Z -- ./recipe.yml $(BASE_IMAGE) $(CONT_IMG)

check:
	PYTHONPATH=$(CURDIR) pytest-3 --full-trace -l -v $(TEST_TARGET)

shell:
	podman run --rm -ti -v $(CURDIR):/src:Z -w /src $(CONT_IMG) bash

check-pypi-packaging:
	podman run --rm -ti -v $(CURDIR):/src:Z -w /src $(CONT_IMG) bash -c '\
		set -x \
		&& rm -f dist/* \
		&& python3 ./setup.py sdist bdist_wheel \
		&& pip3 install dist/*.tar.gz \
		&& ansible-bender --help \
		&& ansible-bender build --help \
		&& pip3 show $(PY_PACKAGE) \
		&& twine check ./dist/* \
		&& python3 -c "import ansible_bender; ansible_bender.__version__.startswith(\"0.3.1\")" \
		&& pip3 show -f $(PY_PACKAGE) | ( grep test && exit 1 || :) \
		'

#FIXME: try outer container to be rootless
#       build tests image
#       run tests as an unpriv user
# TODO: podman inside needs to use vfs storage driver
check-smoke:
	sudo podman run --net=host --rm -ti -v $(CURDIR):/src:Z -w /src registry.fedoraproject.org/fedora:29 bash -c '\
		dnf install -y buildah podman \
		&& podman pull docker.io/library/python:3-alpine \
		&& pip3 install . \
		&& ansible-bender build ./tests/data/basic_playbook.yaml docker.io/library/python:3-alpine test'
