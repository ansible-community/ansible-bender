TEST_TARGET := ./tests/
BASE_IMAGE := registry.fedoraproject.org/fedora:29
PY_PACKAGE := ansible-bender
# container image with ab inside
CONT_IMG := $(PY_PACKAGE)
ANSIBLE_BENDER := python3 -m ansible_bender.cli

build-ab-img: recipe.yml
	$(ANSIBLE_BENDER) build -- ./recipe.yml $(BASE_IMAGE) $(CONT_IMG)

check:
	PYTHONPATH=$(CURDIR) PYTHONDONTWRITEBYTECODE=yes pytest-3 --cov=ansible_bender -l -v $(TEST_TARGET)

check-in-container:
	podman run -ti --rm \
		--tmpfs /tmp:rw,exec,nosuid,nodev,size=1000000k \
		--privileged \
		-e CGROUP_MANAGER=cgroupfs \
		-v $(CURDIR):/src \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-w /src \
		$(CONT_IMG) \
		make check TEST_TARGET='$(TEST_TARGET)'

shell:
	podman run --rm -ti -v $(CURDIR):/src:Z -w /src $(CONT_IMG) bash

push-image-to-dockerd:
	podman push $(CONT_IMG) docker-daemon:ansible-bender:latest

run-in-okd:
	ansible-playbook -vv ./contrib/run-in-okd.yml
	oc get all
	sleep 3  # give oc time to spin the container
	oc logs -f pod/ab-in-okd-1-build

check-in-okd:
	ansible-playbook -vv ./contrib/check-in-okd.yml
	oc get all
	sleep 2
	oc logs -f pod/ab

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
	podman run --net=host --rm -ti -v $(CURDIR):/src:Z -w /src registry.fedoraproject.org/fedora:29 bash -c '\
		dnf install -y buildah podman \
		&& podman pull docker.io/library/python:3-alpine \
		&& pip3 install . \
		&& ansible-bender build ./tests/data/basic_playbook.yaml docker.io/library/python:3-alpine test'

# for CI
check-in-docker:
	docker run --rm --privileged -v $(CURDIR):/src -w /src \
		-v /var/run/docker.sock:/var/run/docker.sock \
		--tmpfs /tmp:rw,exec,nosuid,nodev,size=1000000k \
		$(BASE_IMAGE) \
		bash -c " \
			set -x \
			&& dnf install -y ansible make \
			&& ansible-playbook -i 'localhost,' -e ansible_python_interpreter=/usr/bin/python3 -e test_mode=yes -c local ./recipe.yml \
			&& id \
			&& pwd \
			&& podman info \
			&& buildah info || : \
			&& make check"

# we need exec since we create arbitrary buildah binary
check-in-docker-easy:
	docker run -ti --rm \
		-v $(CURDIR):/src -w /src \
		-e CGROUP_MANAGER=cgroupfs \
		--privileged \
		-v /var/run/docker.sock:/var/run/docker.sock \
		--tmpfs /tmp:rw,exec,nosuid,nodev,size=1000000k \
		$(CONT_IMG) \
		make check TEST_TARGET='$(TEST_TARGET)'
