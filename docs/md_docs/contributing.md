# Contributing to ansible-bender

## Setting up your local development environment

Please make sure to follow bender's installation process:
https://github.com/ansible-community/ansible-bender#installation

For local development, you'll need a few more packages. All of them are
listed in
[setup.cfg](https://github.com/ansible-community/ansible-bender/blob/master/setup.cfg):

1. To run bender from git, you need `setuptools_scm`
2. Test suite is using `pytest` and `flexmock`

A lot of development automation is done in the
[Makefile](https://github.com/ansible-community/ansible-bender/blob/master/Makefile)
so make sure that you have GNU make installed.

Since bender is so closely tight to podman and buildah, it works only on linux.


## Tests

A good way to verify that everything works fine is to run the test suite in your local environment:
```
$ make check
PYTHONPATH=/home/me/path/to/ansible-bender PYTHONDONTWRITEBYTECODE=yes pytest-3 --cov=ansible_bender -l -v ./tests/
=============================== test session starts =====================================
platform linux -- Python 3.7.4, pytest-3.9.3, py-1.7.0, pluggy-0.8.1 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/me/path/to/ansible-bender, inifile:
plugins: celery-4.3.0, cov-2.6.0
collected 61 items

tests/functional/test_buildah.py::test_output PASSED                       [  1%]
tests/functional/test_buildah.py::test_build_basic_image PASSED            [  3%]
tests/functional/test_buildah.py::test_build_basic_image_with_env_vars     [....]
...
```

You can also run the test suite in a container:
```
$ make build-ab-img && make check-in-container
```


### CI

Bender is using [packit project](https://packit.dev/) for continuous integration.

Related files:
* .packit.yaml — root config file for packit
* .fmf/ — packit utilies [fmf]() project under the hood and this dir is required for fmf to function
* tests/ci.fmf — definition of tests to run in Packit's CI System - Testing Farm
* ci.yaml — Ansible playbook to set up the testing environment so bender's test suite can run


## Install the development version

You can install your development checkout like this:
```
$ cd local/git/checkout/of/bender/
$ pip3 install --user -e .
```


## Run bender directly from git

It's really easy:
```
$ PAYTHONPATH=/home/me/local/git/checkout/of/bender/ python3 -m ansible_bender.cli --help
```
