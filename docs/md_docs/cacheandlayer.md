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