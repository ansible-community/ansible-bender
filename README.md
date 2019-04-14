# ansible-bender
[![Build Status](https://dev.azure.com/nereone/ab/_apis/build/status/TomasTomecek.ansible-bender?branchName=master)](https://dev.azure.com/nereone/ab/_build/latest?definitionId=1&branchName=master)

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


## Features:

* You can build your container images with buildah as a backend.
* Ansible playbook is your build recipe.
* You are able to set various image metadata via CLI or as specific Ansible vars:
  * working directory
  * environment variables
  * labels
  * user
  * default command
  * exposed ports
* You can do volume mounts during build.
* Caching mechanism:
  * Every task result is cached as a container image layer.
  * You can turn this off with `--no-cache`.
  * You can disable caching from a certain point by adding a tag `no-cache` to a task.
* You can stop creating new image layers by adding tag `stop-layering` to a task.
* If an image build fails, it's committed and named with a suffix `-failed` (so
  you can take a look inside and resolve the issue).
* The tool tries to find python interpreter inside the base image.
* You can push images you built to remote locations such as:
  * a registry, a tarball, docker daemon, ...
  * [`podman push`](https://github.com/containers/libpod/blob/master/docs/podman-push.1.md) is used to perform the push.


## Interface

Ansible-bender has these commands:

Command | Description
--------|------------
`build` | build a new container image using selected playbook
`list-builds` | list all builds
`get-logs` | display build logs
`inspect` | provide detailed metadata about the selected build
`push` | Push images you built to remote locations.


## Installation

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

* [Podman](https://github.com/containers/libpod)
* [Buildah](https://github.com/containers/buildah)
* [Ansible](https://github.com/ansible/ansible)
  * Ansible needs to be built against python 3
* Python 3

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


## Configuration

You can configure ansible-bender and set metadata on your final image, in order
to do that, please check out [docs/configuration.md](docs/configuration.md).


### Ansible roles

If you are using roles in your playbook and they are in a non-standard place,
you can utilize `ANSIBLE_ROLES_PATH` environment variable to tell ansible where
your roles lives. Bender does not tamper with environment variables, all are
passed to ansible-playbook.


## Debugging Bender

It may happen there is something wrong in your setup or the tooling Bender is
relying on is not in the best shape. The best way to find the root cause is to
run Bender in debug mode and run ansible as verbosely as possible:
```
$ ansible-bender --debug build --extra-ansible-args='-vvvvvv'
```


## Usage

Typing `ansible-bender` can take some time, consider adding an alias into your
shell rc file:
```
alias ab="ansible-bender"
```

### Building images

There is a simple playbook present in the root of this repository to showcase the functionality:
```bash
$ ansible-bender build ./simple-playbook.yaml

PLAY [Demonstration of ansible-bender functionality] ****************************************

TASK [Gathering Facts] **********************************************************************
ok: [a-very-nice-image-20190302-153257279579-cont]

TASK [Run a sample command] *****************************************************************
changed: [a-very-nice-image-20190302-153257279579-cont]
caching the task result in an image 'a-very-nice-image-20193302-153306'

TASK [Stat a file] **************************************************************************
ok: [a-very-nice-image-20190302-153257279579-cont]
caching the task result in an image 'a-very-nice-image-20193302-153310'

PLAY RECAP **********************************************************************************
a-very-nice-image-20190302-153257279579-cont : ok=3    changed=1    unreachable=0    failed=0

Getting image source signatures

Skipping blob 767f936afb51 (already present): 4.46 MiB / 4.46 MiB [=========] 0s

Skipping blob b211a7fc6e85 (already present): 819.00 KiB / 819.00 KiB [=====] 0s

Skipping blob 8d092d3e44bb (already present): 67.20 MiB / 67.20 MiB [=======] 0s

Skipping blob 767f936afb51 (already present): 4.46 MiB / 4.46 MiB [=========] 0s

Skipping blob b211a7fc6e85 (already present): 819.00 KiB / 819.00 KiB [=====] 0s

Skipping blob 8d092d3e44bb (already present): 67.20 MiB / 67.20 MiB [=======] 0s

Skipping blob 492c5c55da84 (already present): 4.50 KiB / 4.50 KiB [=========] 0s

Skipping blob 6f55b6e55d8a (already present): 6.15 MiB / 6.15 MiB [=========] 0s

Skipping blob 80ea48511c5d (already present): 1021.00 KiB / 1021.00 KiB [===] 0s

Copying config 6b6dc5878fb2: 0 B / 5.15 KiB [----------------------------------]
Copying config 6b6dc5878fb2: 5.15 KiB / 5.15 KiB [==========================] 0s
Writing manifest to image destination
Storing signatures
6b6dc5878fb2c2c10099adbb4458c2fc78cd894134df6e4dee0bf8656e93825a
Image 'a-very-nice-image' was built successfully \o/
```

This is how the playbook looks:
```yaml
---
- name: Demonstration of ansible-bender functionality
  hosts: all
  vars:
    ansible_bender:
      base_image: python:3-alpine

      working_container:
        volumes:
          - '{{ playbook_dir }}:/src'

      target_image:
        name: a-very-nice-image
        working_dir: /src
        labels:
          built-by: '{{ ansible_user }}'
        environment:
          FILE_TO_PROCESS: README.md
  tasks:
  - name: Run a sample command
    command: 'ls -lha /src'
  - name: Stat a file
    stat:
      path: "{{ lookup('env','FILE_TO_PROCESS') }}"
```

As you can see, the whole build processed is configured by the variable
`ansible_bender`.

If we rerun the build again, we can see that ab loads every task from cache:
```bash
$ ansible-bender build ./simple-playbook.yaml

PLAY [Demonstration of ansible-bender functionality] ****************************************

TASK [Gathering Facts] **********************************************************************
ok: [a-very-nice-image-20190302-153526013757-cont]

TASK [Run a sample command] *****************************************************************
loaded from cache: '7c69668c42987446cc78adbf6620fc2faf90ad10c3497662fe38940dd6de998f'
skipping: [a-very-nice-image-20190302-153526013757-cont]

TASK [Stat a file] **************************************************************************
loaded from cache: '4a4f54285928c03eea65745ee9feead88026c780a40126d94e79d5842bcdbe62'
skipping: [a-very-nice-image-20190302-153526013757-cont]

PLAY RECAP **********************************************************************************
a-very-nice-image-20190302-153526013757-cont : ok=1    changed=0    unreachable=0    failed=0

Getting image source signatures

Skipping blob 767f936afb51 (already present): 4.46 MiB / 4.46 MiB [=========] 0s

Skipping blob b211a7fc6e85 (already present): 819.00 KiB / 819.00 KiB [=====] 0s

Skipping blob 8d092d3e44bb (already present): 67.20 MiB / 67.20 MiB [=======] 0s

Skipping blob 492c5c55da84 (already present): 4.50 KiB / 4.50 KiB [=========] 0s
Skipping blob 767f936afb51 (already present): 4.46 MiB / 4.46 MiB [=========] 0s
Skipping blob 6f55b6e55d8a (already present): 6.15 MiB / 6.15 MiB [=========] 0s
Skipping blob b211a7fc6e85 (already present): 819.00 KiB / 819.00 KiB [=====] 0s
Skipping blob 80ea48511c5d (already present): 1021.00 KiB / 1021.00 KiB [===] 0s
Skipping blob 8d092d3e44bb (already present): 67.20 MiB / 67.20 MiB [=======] 0s
Skipping blob 5f70bf18a086 (already present): 1.00 KiB / 1.00 KiB [=========] 0s
Skipping blob 492c5c55da84 (already present): 4.50 KiB / 4.50 KiB [=========] 0s

Skipping blob 6f55b6e55d8a (already present): 6.15 MiB / 6.15 MiB [=========] 0s

Skipping blob 80ea48511c5d (already present): 1021.00 KiB / 1021.00 KiB [===] 0s

Skipping blob 5f70bf18a086 (already present): 1.00 KiB / 1.00 KiB [=========] 0s

Copying config 354752b97084: 0 B / 5.26 KiB [----------------------------------]
Copying config 354752b97084: 5.26 KiB / 5.26 KiB [==========================] 0s
Writing manifest to image destination
Storing signatures
354752b97084fcf349a28a2f66839d270e728559883dd1edb5ec22e8c9c6adb9
Image 'a-very-nice-image' was built successfully \o/
```


### Listing builds

We can list builds we have done:
```bash
$ ansible-bender list-builds
  BUILD ID  IMAGE NAME         STATUS    DATE                        BUILD TIME
----------  -----------------  --------  --------------------------  --------------
         1  a-very-nice-image  done      2019-03-02 16:07:47.471912  0:00:12.347721
         2  a-very-nice-image  done      2019-03-02 16:07:58.858699  0:00:06.242378
```


### Getting logs of a build

Wanna check build logs sometime later? No problem!
```bash
$ ansible-bender get-logs 2

PLAY [Demonstration of ansible-bender functionality] *********************************

TASK [Gathering Facts] ***************************************************************
ok: [a-very-nice-image-20190302-160751828671-cont]

TASK [Run a sample command] **********************************************************
loaded from cache: 'cd27cfb71a161f3333232b97cc6b2a89354ff52de71bce9058c52cdf536735f9'
skipping: [a-very-nice-image-20190302-160751828671-cont]

TASK [Stat a file] *******************************************************************
loaded from cache: '89ba4efc31358d688f035bf8159d900f1552314f0af6bf6c338b4897da593ccf'
skipping: [a-very-nice-image-20190302-160751828671-cont]

PLAY RECAP ***************************************************************************
a-very-nice-image-20190302-160751828671-cont : ok=1    changed=0    unreachable=0    failed=0
```


### Locating built images with podman

Once they are built, you can use them with podman right away:
```bash
$ podman images a-very-nice-image
REPOSITORY                    TAG      IMAGE ID       CREATED         SIZE
localhost/a-very-nice-image   latest   5202048d9a0e   2 minutes ago   83.5 MB
```


### Buildah configuration

If you are familiar with podman and buildah, you know that you can
[configure](https://github.com/containers/buildah/blob/master/docs/buildah.md#files)
these tools. Ansible-bender doesn't change this configuration in any way so
it's up to you how you set up buildah and podman. The same applies for running
ansible-bender as root or not: buildah allows you to utilize rootless
containers.

My suggestion is to use the overlay storage backend. Vfs backend is slow and
inefficient.


### Caching mechanism

Ansible bender has a caching mechanism. It is enabled by default. ab caches
task results (=images). If a task content did not change and the base image is
the same, the layer is loaded from cache instead of being processed again. This
doesn't work correctly with tasks which process file: ab doesn't handle files
yet.

You are able to control caching in two ways:

 * disable it completely by running `ab build --no-cache`
 * or adding a tag to your task named `no-cache` — ab detects such tag and
   will not try to load from cache


### Layering mechanism

When building your image by default, every task (except for setup) is being
cached as an image layer. This may have bad consequences on storage and
security: there may be things which you didn't want to have cached nor stored
in a layer (certificates, package manager metadata, build artifacts).

ab allows you to easily disable layering mechanism. All you need to do is to
add a tag `stop-layering` to a task which will disable layering (and caching)
for that task and all the following ones.


### Ansible-bender in OKD

Recently I started experimenting with running ab inside [OpenShift
origin](https://github.com/openshift/origin) — imagine that you'd be able to
build images in your cluster, using Ansible playbooks as definitions.

Openshift by default runs its pods in a
[restrictive](https://blog.openshift.com/understanding-service-accounts-sccs/)
environment. In the proof of concept I was forced to run ab in a privileged
pod. In the end, the whole test suite is passing in that privileged pod.
