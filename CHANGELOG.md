# 0.6.0

## Features

* You can specify a user to be used during the build process (`--build-user`). (Thanks to @11mariom #122)

## Bug fixes

* Bender is able to correctly process multiple build volumes. (Thanks to @11mariom #118)


# 0.5.3

Thank you for contributions from @jamescassell and @alexgarel!

## Bug fixes

* Bender now correctly picks up all cached layers and does not display an error
  message: `Error: could not get runtime: error creating runtime static files
  directory /var/lib/containers/storage/libpod: mkdir
  /var/lib/containers/storage/libpod: permission denied`. This was coming from
  podman so we switched to buildah to perform checks for presence of layers.
* A name of a working container now contains month digits instead of minutes as
  one would expect. (How come that no one noticed?)

## Minor

* README now contains a bit of documentation for limitations of rootless mode.


# 0.5.2

## Bug fixes

* Workaround an issue with Ansible when SELinux is being used and libselinux
  python bindings are not present, ansible-playbook freezes for a couple of
  minutes.
  * https://bugzilla.redhat.com/show_bug.cgi?id=1696706
  * https://github.com/ansible-community/ansible-bender/issues/101

## Minor

* Document how to make Ansible roles available during a build if they are on a
  custom path.


# 0.5.1

## Bug fixes

* When pushing a build using the `push` command, bender now picks the correct
  image with metadata, instead of the last layer.
* Variables are now expanded recursively. This means that when you define a variable in `vars` section, you can use it in other variables.

## Minor

* Documentation updates.


# 0.5.0

## Breaking changes

* Option `--labels` was renamed to `--label` to match other container tooling.


## Features

* Ansible-bender can now be configured using Ansible variables. For more info,
  please [read the documentation](/docs/configuration.md)
  * Given this change, base image and target image name are now optional
    arguments of the `build` command.
* Bender now uses more candidates when searching for python interpreter in the
  base image, namely `/usr/bin/python3.7` and so on.
* You can now set annotations on the target image.
* When bender invokes a playbook against a container, it now changes hosts
  variable (in a copy), so that it's not accidentally executed in localhost
  environment.
* Json schema is now used to validate input.
* Before starting the build process, bender checks if the container backend
  works.


## Bug fixes

* When ansible-playbook command uses python 2, bender refuses to continue since
  the build will not work.
* Errors are now being properly logged when bender looks for python interpreter
  in the base image.
* There was a need for a compatibility fix with buildah 1.7.
* A build will terminate if there was an exception thrown during the caching or
  layering process.
* Bender will not try to load non-existent layers from cache.


# 0.4.0

Ansible-bender now uses Azure Pipelines as a CI system.

## Features

* There were updates to documentation in README:
  * Info about vfs and overlay buildah storage backends.
  * Rootless containers.
  * How you can use base images with python2.
  * Requirements of ansible-bender.
* Bender now produces a more clear message when a base image doesn't have a
  python interpreter.
* You are now able to pass path to the python interpreter inside the base image
  via CLI.

## Bug fixes

* Bender now uses more buildah commands instead of podman.
* If bender is invoked with a non-root user, the ansible-playbook session is
  now wrapped with `buildah unshare`.
* Don't print to error log when an image is being pulled.


# 0.3.2

I experimented with running ansible-bender inside an OpenShift pod. Details can
be found in a Makefile and in the `contrib/` directory.

## Bug fixes

* Ansible-bender is now able to pull base images properly again if they are not
  present before a build.
* `podman` is now used to perform `inspect`.
* Working container name was improved to be more safe.


# 0.3.1

## Breaking changes

* Since our executable, `ab`, conflicted with a binary from `httpd` package, I
  decided to rename it to `ansible-bender`. Please add a shell alias if you
  want ab back.

## Features

* You can pass extra arguments to `ansible-playbook` command via
  `--ansible-extra-args=`. Use it with caution!
* Python packaging was improved, thanks to great help from @webknjaz

## Bug fixes

* Ansible-bender now correctly processes build volumes even when a layer is
  loaded from cache.


# 0.3.0

## Features

* There is a new command available: `push`. You can push the images you built
  to remote locations. This is built on top of `podman push` command, for more
  info please see manpages podman-push(1) or skopeo(1).
* Inspecting a build now produces more info: playbook path, ID of the image, build volumes.

## Bug fixes

* For file-related actions, when ansible reports changed=False, the respective
  layer will be now loaded from cache.


# 0.2.1

## Bug fixes

* Correctly recreate working container when loading a layer from cache.
* When ab is installed using pip on Fedora 29, it wasn't able to import itself
  when invoked from the callback plugin. This is now resolved.


# 0.2.0

Renamed to `ansible-bender`, the binary name was left intact.

## Features

 * Failed builds are commited as `-failed`.
 * The tool tries to find python interpreter inside the base image.
 * Added command `list-builds`.
 * Added command `get-logs`.
 * Added command `inspect`.
 * Implemented a caching mechanism:
   * Limitation of caching are file tasks: ansible can't detect that a file wasn't changed and reports it changed.
     This means that ab is not able to load such result from cache.
   * Caching can be controled by a tag `no-cache` which you can put into a task.
 * You can disable layering either by build's option `--no-cache` or adding a tag `stop-Layering` to a task.
 * Multiple user experience, output, polish changes.


# 0.1.0

Initial release!

## Features

* You can build your container images with buildah as a backend.
* You are able to set various image metadata via CLI:
  * working directory
  * environment variables
  * labels
  * user
  * default command
  * exposed ports
* You can do volume mounts during build.

