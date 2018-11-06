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

