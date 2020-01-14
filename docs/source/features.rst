Features
=========

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
  * You can turn this off with ``--no-cache``.
  * You can disable caching from a certain point by adding a tag ``no-cache`` to a task.
* You can stop creating new image layers by adding tag ``stop-layering`` to a task.
* If an image build fails, it's committed and named with a suffix ``-[TIMESTAMP]-failed`` (so
  you can take a look inside and resolve the issue).
* The tool tries to find python interpreter inside the base image.
* You can push images you built to remote locations such as:

  * a registry, a tarball, docker daemon, ...
  * `podman push <https://github.com/containers/libpod/blob/master/docs/podman-push.1.md>`_ is used to perform the push.