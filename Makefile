TEST_TARGET := ./tests/

check:
	PYTHONPATH=$(CURDIR) pytest-3 -v $(TEST_TARGET)

check-pypi-packaging:
	podman run --rm -ti -v $(CURDIR):/src -w /src registry.fedoraproject.org/fedora:28 bash -c '\
		pip3 install . \
		&& ab --help \
		&& ab build --help'

check-install-010:
	podman run --rm -ti -v $(CURDIR):/src -w /src registry.fedoraproject.org/fedora:28 bash -c '\
		dnf install -y git \
		&& pip3 install --user git+https://github.com/TomasTomecek/ab@0.1.0 \
		&& ab --help \
		&& ab build --help'
