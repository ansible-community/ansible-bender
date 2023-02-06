# 0.10.1

* A fixup release: twine refused an upload due to incorrect URL (fix: 216ff3f101494daf1bdaf4f427fe17fa108e100d)


# 0.10.0

## Features

* File operations are now also cached (examples: "file", "copy", "synchronize", "unarchive", and "template"), by [@kjohnson0451](https://github.com/kjohnson0451), [#246](https://github.com/ansible-community/ansible-bender/pull/246)
* Use `AnsibleVarsParser` class to process ansible variables, by [@quietjoy](https://github.com/quietjoy), [#287](https://github.com/ansible-community/ansible-bender/pull/287)
  * It allows `ansible_bender` variables to be specified across group and host var files.
* Enable passing extra args to `podman run` and `ansible run`, by [@ArmaanT](https://github.com/ArmaanT), [#278](https://github.com/ansible-community/ansible-bender/pull/278)
* `import_playbook` statements are now supported, by [@themkat](https://github.com/themkat), [#268](https://github.com/ansible-community/ansible-bender/pull/268)
* Python interpreter locations are now cached for each base image, by [@themkat](https://github.com/themkat), [#267](https://github.com/ansible-community/ansible-bender/pull/267)

## Fixes

* SELinux checks are now dropped since they are no longer relevant, by [@quietjoy](https://github.com/quietjoy), [#285](https://github.com/ansible-community/ansible-bender/pull/285)
* Vagrant development environment now works again, by [@quietjoy](https://github.com/quietjoy), [#286](https://github.com/ansible-community/ansible-bender/pull/286)
* Qualified image names are now used to reference images instead of short-names, by [@tpo](https://github.com/tpo), [#263](https://github.com/ansible-community/ansible-bender/pull/263)


# 0.9.0

## Features

* Make it possible to set entrypoint for a working_container, by [@Smeds](https://github.com/Smeds), [#232](https://github.com/ansible-community/ansible-bender/pull/232)

* Add sphinx based docs with read-the-docs theme for ansible-bender, by [@kmehant](https://github.com/kmehant), [#215](https://github.com/ansible-community/ansible-bender/pull/215)
  * Available at https://ansible-community.github.io/ansible-bender/build/html/index.html

## Fixes

* Make `buildah_from_extra_args` actually work, by [@TomasTomecek](https://github.com/TomasTomecek), [#217](https://github.com/ansible-community/ansible-bender/pull/217)

* Python packaging was polished, by [@gordonmessmer](https://github.com/gordonmessmer), [#227](https://github.com/ansible-community/ansible-bender/pull/227), [224](https://github.com/ansible-community/ansible-bender/pull/224), [#225](https://github.com/ansible-community/ansible-bender/pull/225)


# 0.8.1

## Fixes

* `clean` command now works properly.
* If bender can't create a container, a useful error message is now being
  printed.

## Features

* Warn when you request a change to UID while running in rootless mode (user
  namespaces are tricky).
* If an image build failed, bender tagged the image with a `-failed` suffix so
  it could be inspected further. Now bender also prepends timestamp so one
  image is not being overwritten over and over.

## Minor

* Improvements to documentation in README and `--help` output.


# 0.8.0

Thank you to all the contributors! You are awesome!

And special thanks to @kmehant, our [Red Hat Open Source Contest 2019](https://research.redhat.com/red-hat-open-source-contest/) student.

## Features

* You can now pass extra arguments to `buildah from` call when bender creates
  new build container. This can be done from CLI using
  `--extra-buildah-from-args` option of build command or in the playbook:
  `vars → ansible-bender → buildah_from_extra_args`. Thanks to @jordemort #140
* One can print bender's version using `-V/--version` options.
* The final image build by bender can now be squashed — all layers merged into
  one. This can be done with the `--squash` option or in the playbook: `vars →
  ansible-bender → squash`. @jordemort #154
* Entrypoints now can be set! Aside from default container commands. Similar
  drill: `--entrypoint` or `vars → ansible-bender → target_image → entrypoint`,
  thanks you, @slopedog #155
* Build times in `list-builds` are now more readable, enjoy! Thanks to @kmehant
  #161
* Bender can now locate platform-python of RHEL 8 and CentOS 8, thanks to
  @hhenkel #171
* When running bender in debug mode (--debug), ansible stdout callback plugin
  is set to debug (`ANSIBLE_STDOUT_CALLBACK=debug`). @kmehant #175
* Ansible executes a playbook in the buildah container using `buildah run`
  command. Before bender gets to that point, it tries to create a no-op
  container (`buildah from --name $container $base_image && buildah run
  $container true`) first to verify that the container runtime is correctly set
  up. @kmehant #174
* We have two new subcommands:
  * `init` — create a template playbook in the current working directory so you
    can get on-board bender's train more easily. @kmehant #184
  * `clean` — clean images from database which are no longer present on disk
    @kmehant #180

## Bug fixes

* Buildah 1.7.3 introduced a backwards-incompatible change to `commit` command
  which required changes in bender's code. Bender is now able to work with
  both: buildah `< 1.7.3` and `>= 1.7.3`. CentOS 8.0 and RHEL 8.0 have buildah
  `< 1.7.3`.
* Bender is using file locking when using its database (`~/.cache/ab/db.json`),
  the locks are now atomic thanks to @kmehant #176
* When you set bender-specific variables in your playbook (`vars →
  ansible-bender`) and there is a typo in any of the variables or the variable
  is not recognized, bender exits and informs you about this problem — we have
  implemented this to prevent typos in the configuration so that you would not
  be able to build invalid images. @kmehant #189
* Bender no longer prints output from buildah pull as errors. @kmehant #195

## Minor

* [Contribution guide](/CONTRIBUTING.md) is now placed in the upstream repo.
* You can now invoke ansible-bender directly from the upstream git repo using
  the common python way:
  ```
  $ python3 -m ansible_bender --help
  ```
  @kmehant #160
* Bender is now using [Packit project](https://packit.dev/) for continuous integration.


# 0.7.0

## Changes

* Intermediate image layers are no longer tagged with a name. This was required
  by buildah, which is no longer the case since the 1.8 release. You can have
  the old behavior by adding `verbose_layer_names: true` to the root of the
  configuration.

## Bug fixes

* `list-builds` should no longer error out after an upgrade.
* Bender incorrectly printed output of `buildah inspect $base_image` which
  cluttered the output a lot - that's no longer the case.


# 0.6.1

## Bug fixes

* Make bender work with ansible 2.8.

## Minor

* Test bender in vagrant VMs against ansible 2.7 and 2.8.


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

