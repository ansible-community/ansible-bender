check:
	PYTHONPATH=$(CURDIR) pytest-3 -v ./tests/

check-pypi-packaging:
	podman run --rm -ti -v $(CURDIR):/src -w /src registry.fedoraproject.org/fedora:28 bash -c '\
		pip3 install . \
		&& ab --help \
		&& ab build --help'
