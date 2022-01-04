# Installation

```
$ pip3 install ansible-bender
```

If you are brave enough, please install bender directly from git master:
```
$ pip3 install git+https://github.com/ansible-community/ansible-bender
```

If `pip3` command is not available on your system, you can run pip like this:
```
$ python3 -m pip install ...
```


### Requirements (host)

Pip takes care of python dependencies, but ansible-bender also requires a few
binaries to be present on your host system:

* [Podman](https://podman.io/getting-started/installation)
* [Buildah](https://github.com/containers/buildah/blob/master/install.md)
* [crun](https://github.com/containers/crun)
* [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html)
  * Ansible needs to be built against python 3
* Python 3.6 or later (python 3.5 or earlier are not supported and known not
  to be working)

Last two requirements can be pretty tough: you can always run bender in a
privileged container.


#### Setting up buildah and podman

If you run ansible-bender as root, you don't need to set up anything. Just
install the packages and you are good to go. This is the preferred way —
buildah and podman are much more efficient when using the in-kernel overlay
filesystem and you will encounter [less issues than with the rootless
mode](https://github.com/containers/libpod/blob/master/rootless.md).

On the other hand, if you want to utilize [the rootless
mode](https://github.com/containers/libpod/blob/master/docs/podman-create.1.md#rootless-containers),
you need to set up the UID mapping. It is documented in
[podman's](https://github.com/containers/libpod/blob/master/troubleshooting.md#10-podman-fails-to-run-in-user-namespace-because-etcsubuid-is-not-properly-populated)
documentation. All you need to do is to add an entry into /etc/subuid and
/etc/subgid:

```bash
$ sudo sh -c "printf \"\n$(whoami):100000:65536\n\" >>/etc/subuid"
$ sudo sh -c "printf \"\n$(whoami):100000:65536\n\" >>/etc/subgid"
```

You should consult [podman's troubleshooting
guide](https://github.com/containers/libpod/blob/master/troubleshooting.md) if
you are running into issues.


### Requirements (base image)

* python interpreter — ansible-bender will try to find it (alternatively you
  can specify it via `--python-interpreter`).
  * It can be python 2 or python 3 — on host, you have to have python 3 but
    inside the base image, it doesn't matter — Ansible is able to utilize
    python 2 even if it's invoked with python 3 on the control machine.


### Requirements (Ansible playbook)

None.

Bender copies the playbook you provide so that it can be processed. `hosts`
variable is being overwritten in the copy and changed to the name of the
working container — where the build happens.  So it doesn't matter what's the
content of the hosts variable.
