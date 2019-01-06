# ansible-bender

This is a tool which bends containers using [Ansible](https://github.com/ansible/ansible)
[playbooks](https://docs.ansible.com/ansible/latest/user_guide/playbooks.html) and turns them into images.
It has a pluggable builder selection — it is up to you to pick the tool which
will be used to construct your container image. Right now the only supported
builder is [buildah](https://github.com/projectatomic/buildah). [More to come
in future](#todo-past-010). ansible-bender (ab) relies on [Ansible connection
plugins](https://docs.ansible.com/ansible/2.6/plugins/connection.html) for performing builds.

tl;dr Ansible is the frontend, buildah is the backend.

I described this concept in these blog posts:
* [Building containers with buildah and ansible](https://blog.tomecek.net/post/building-containers-with-buildah-and-ansible/).
* [Ansible and Podman Can Play Together Now](https://blog.tomecek.net/post/ansible-and-podman-can-play-together-now/)

You may be asking: why not
[ansible-container](https://github.com/ansible/ansible-container)? Ansible bender is
actually heavily inspired by ansible-container: the main distinction is that
ansible-container covers the complete lifecycle of a containerized application
while ab takes care of image builds only.


**Status**: ready to use


## Features:

* You can build your container images with buildah as a backend.
* Ansible playbook is your build recipe.
* You are able to set various image metadata via CLI:
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
* If an image build fails, it's comitted and named with a suffix `-failed` (so
  you can take a look inside and resolve the issue).
* The tool tries to find python interpreter inside the base image.
* You can push images you built to remote locations such as:
  * a registry, a tarball, docker daemon, ...
  * [`podman push`](https://github.com/containers/libpod/blob/master/docs/podman-push.1.md) is used to perform the push.


## Interface

ab has these commands:

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

Ansible bender supports python 3 only. This means that you need to have a
python3 interpretter inside your base image.


## Usage

You may noticed that I refer to `ansible-bender` as ab. That was the initial
name and I used to it. I recommand adding an alias into your shell rc file:
```
alias ab="ansible-bender"
```

### Building images

If you clone this repository, you can utilize a simple playbook I am using for testing:
```
$ ansible-bender build -e SOME=VALUE -l some=other-value -- ./tests/data/basic_playbook.yaml docker.io/library/python:3-alpine this-is-my-image

PLAY [all] ************************************************************************************************************************

TASK [Gathering Facts] ************************************************************************************************************
ok: [this-is-my-image-20181031-121858148338-cont]

TASK [print local env vars] *******************************************************************************************************
ok: [this-is-my-image-20181031-121858148338-cont] => {
    "msg": "/tmp/ab1nsv_c9b/ansible.cfg,,"
}
caching the task result in an image 'this-is-my-image-20181931-121904'

TASK [print all remote env vars] **************************************************************************************************
ok: [this-is-my-image-20181031-121858148338-cont] => {
    "msg": {
        "GPG_KEY": "0D96DF4D4110E5C43FBFB17F2D347EA6AA65421D",
        "HOME": "/root",
        "LANG": "C.UTF-8",
        "PATH": "/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "PWD": "/",
        "PYTHON_PIP_VERSION": "18.1",
        "PYTHON_VERSION": "3.7.0",
        "SHLVL": "1",
        "SOME": "VALUE"
    }
}
caching the task result in an image 'this-is-my-image-20181931-121905'

TASK [Run a sample command] *******************************************************************************************************
changed: [this-is-my-image-20181031-121858148338-cont]
caching the task result in an image 'this-is-my-image-20181931-121908'

TASK [create a file] **************************************************************************************************************
changed: [this-is-my-image-20181031-121858148338-cont]
caching the task result in an image 'this-is-my-image-20181931-121912'

PLAY RECAP ************************************************************************************************************************
this-is-my-image-20181031-121858148338-cont : ok=5    changed=2    unreachable=0    failed=0

Getting image source signatures
Skipping fetch of repeat blob sha256:df64d3292fd6194b7865d7326af5255db6d81e9df29f48adde61a918fbd8c332
Skipping fetch of repeat blob sha256:beefb6beb20fa287cfcfaf083c0fda606f9c7f4b2830a286a50f1bbcacd52cf3
Skipping fetch of repeat blob sha256:e2986b5e7ba21a779988ffeb8bd4c0ca5b0fddaaf1ea8a4b02da1c60492f51e4
Skipping fetch of repeat blob sha256:6795dbd93463993b8257a1500534c1fe8566aa79dfc08a03c9d823b26d08b8d8
Skipping fetch of repeat blob sha256:3b3df229744dd8a66aa6713ce8084f529712e96c4d01fa7b0a4cb49fe2e2ebff
Skipping fetch of repeat blob sha256:3e8ad7a0bc8fa42dfb6e11bb57ec6cafd865426b1557e29ee58c4ffd8b077aba
Copying config sha256:bbf10af5c37b2c7f6098f07308df4addcd81598e16d1e432bb5c5b1916c9d912

 0 B / 5.11 KiB [--------------------------------------------------------------]
 5.11 KiB / 5.11 KiB [======================================================] 0s
Writing manifest to image destination
Storing signatures
bbf10af5c37b2c7f6098f07308df4addcd81598e16d1e432bb5c5b1916c9d912
Image 'this-is-my-image' was built successfully \o/
```

The command line is a bit longer. That's because all metadata about our target image is in there:
```
$ ansible-bender build                           \  # this is the command
     -e SOME=VALUE                               \  # -e sets environment variables
     -l some=other-value                         \  # -l sets labels
     --                                          \  # two dashes separate options from arguments
     ./tests/functional/data/basic_playbook.yaml \  # first argument is a path to a playbook
     docker.io/library/python:3-alpine           \  # second one is a base image (and is pulled if it's not present)
     this-is-my-image                            \  # and finally, target image name
```

If we rerun the build again, we can see that ab loads every task from a cache:
```
$ ansible-bender build -e SOME=VALUE -l some=other-value -- ./tests/data/basic_playbook.yaml docker.io/library/python:3-alpine this-is-my-image

PLAY [all] ************************************************************************************************************************

TASK [Gathering Facts] ************************************************************************************************************
ok: [this-is-my-image-20181031-121917088731-cont]

TASK [print local env vars] *******************************************************************************************************
loaded from cache: '2cf027dce668d168f73c67e3aa42175e89c42458f6c5f6844ebf74f3064080d2'
skipping: [this-is-my-image-20181031-121917088731-cont]

TASK [print all remote env vars] **************************************************************************************************
loaded from cache: 'e6b4f418907ca31d5e52e2b971f8224637daa610a1b54467ee2919001d4caf37'
skipping: [this-is-my-image-20181031-121917088731-cont]

TASK [Run a sample command] *******************************************************************************************************
loaded from cache: '96aaa104e30b394652639d56122bbf8bb3ba8e75c1bdf8ea01fa879930c07bc6'
skipping: [this-is-my-image-20181031-121917088731-cont]

TASK [create a file] **************************************************************************************************************
loaded from cache: '91dd37d6c6cf05b5505cb7b799534757c89a5e22230fceff1ad01999c766a2a0'
skipping: [this-is-my-image-20181031-121917088731-cont]

PLAY RECAP ************************************************************************************************************************
this-is-my-image-20181031-121917088731-cont : ok=1    changed=0    unreachable=0    failed=0

Getting image source signatures
Skipping fetch of repeat blob sha256:df64d3292fd6194b7865d7326af5255db6d81e9df29f48adde61a918fbd8c332
Skipping fetch of repeat blob sha256:beefb6beb20fa287cfcfaf083c0fda606f9c7f4b2830a286a50f1bbcacd52cf3
Skipping fetch of repeat blob sha256:e2986b5e7ba21a779988ffeb8bd4c0ca5b0fddaaf1ea8a4b02da1c60492f51e4
Skipping fetch of repeat blob sha256:6795dbd93463993b8257a1500534c1fe8566aa79dfc08a03c9d823b26d08b8d8
Skipping fetch of repeat blob sha256:3b3df229744dd8a66aa6713ce8084f529712e96c4d01fa7b0a4cb49fe2e2ebff
Skipping fetch of repeat blob sha256:eca799d88ff3ae1f5a17bd5569a54f7de3694b3b6a134c16cda1216a3b8a2779
Skipping fetch of repeat blob sha256:4f4fb700ef54461cfa02571ae0db9a0dc1e0cdb5577484a6d75e68dc38e8acc1
Copying config sha256:8eabbd9aef50ae41499a5720ec6a1be6bad29095b278e58fccb9f04c2eaa459a

 0 B / 5.22 KiB [--------------------------------------------------------------]
 5.22 KiB / 5.22 KiB [======================================================] 0s
Writing manifest to image destination
Storing signatures
8eabbd9aef50ae41499a5720ec6a1be6bad29095b278e58fccb9f04c2eaa459a
Image 'this-is-my-image' was built successfully \o/
```


### Listing builds

We can list builds we have done:
```
  BUILD ID  IMAGE NAME        STATUS           DATE                        BUILD TIME
----------  ----------------  ---------------  --------------------------  --------------
         1  this-is-my-image  BuildState.DONE  2018-10-31 12:19:13.847864  0:00:15.699248
         2  this-is-my-image  BuildState.DONE  2018-10-31 12:19:27.341574  0:00:10.252394
```


### Getting logs of a build

Wanna check build logs sometime later? No problem!
```
$ ansible-bender get-logs 2

PLAY [all] ******************************************************************************************************************************************************************

TASK [Gathering Facts] ******************************************************************************************************************************************************
ok: [this-is-my-image-20181031-121917088731-cont]

TASK [print local env vars] *************************************************************************************************************************************************
loaded from cache: '2cf027dce668d168f73c67e3aa42175e89c42458f6c5f6844ebf74f3064080d2'
skipping: [this-is-my-image-20181031-121917088731-cont]

TASK [print all remote env vars] ********************************************************************************************************************************************
loaded from cache: 'e6b4f418907ca31d5e52e2b971f8224637daa610a1b54467ee2919001d4caf37'
skipping: [this-is-my-image-20181031-121917088731-cont]

TASK [Run a sample command] *************************************************************************************************************************************************
loaded from cache: '96aaa104e30b394652639d56122bbf8bb3ba8e75c1bdf8ea01fa879930c07bc6'
skipping: [this-is-my-image-20181031-121917088731-cont]

TASK [create a file] ********************************************************************************************************************************************************
loaded from cache: '91dd37d6c6cf05b5505cb7b799534757c89a5e22230fceff1ad01999c766a2a0'
skipping: [this-is-my-image-20181031-121917088731-cont]

PLAY RECAP ******************************************************************************************************************************************************************
this-is-my-image-20181031-121917088731-cont : ok=1    changed=0    unreachable=0    failed=0
```


### Locating built images with podman

Here is a proof that the image is in there:
```
$ podman images
REPOSITORY                                   TAG                      IMAGE ID       CREATED         SIZE
localhost/this-is-my-image                   latest                   8eabbd9aef50   7 minutes ago   83.1MB
docker.io/library/python                     3-alpine                 cf41883b24b8   3 weeks ago     81.9MB

$ buildah images
IMAGE ID             IMAGE NAME                                               CREATED AT             SIZE
cf41883b24b8         docker.io/library/python:3-alpine                        Oct 10, 2018 00:28     81.9 MB
8eabbd9aef50         localhost/this-is-my-image:latest                        Oct 31, 2018 12:19     83.1 MB
```


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
