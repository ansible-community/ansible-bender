# 0.2.0

* add config for release bot
* 0.2.0 changelog
* disable caching for file tasks
* properly cache and load file-based actions
* update readme
* less verbose buildah when committing layers
* implement explicit layering
* correctly process default db dir
* add a way to stop caching in playbook
* changing user with user namespaces doesn't really work
* todo: implement ansible_args for sake of easier debugging while testing
* db: less useless logging, less churn
* cli: correct obtaining db path candidates
* new test case for caching
* set up logging in app & pass db path to snapshoter
* runtime dir: check only once
* readme: update roadmap
* readme: list subcommands
* add inspect command and more CLI tests
* store logs correctly when a build fails
* list-builds: pretty print state name
* explicitly store layers in DB
* update README
* new CLI command: get-logs
* store logs in the DB
* fix tests
* functional tests: a dedicated runtime db per test case
* do not log output of buildah inspect to debug log
* implement list-builds command
* testing: ignore errors when removing images
* enable overriding path to db via CLI
* store build start and fin times in db
* document caching briefly
* find a-p command
* tests: start spellbook: utilities & DRY
* implement --no-cache
* fix caching tests and test for count
* update todo string
* dont cache failed tasks
* caching: tinker output text
* seems that runtime volumes are not being set
* check that env vars are set in a container
* readme: update todo
* try logging in plugins
* store build container name in db
* fix split_once_or_fail_with, ignore rmi test fails
* tinker caching
* implement caching mechanism
* db: lock when writing
* kickoff callback plugin
* test case for error capturing + clean working cont always
* print stderr output for failed commands
* tests: DRY
* tests: use python 3 alpine base image
* buildah: dont print stderr
* add a test for parallel runs
* store state persistently on disk
* bump to 0.2.0.dev0
* finish the rename
* rename project to ansible-bender
* fail early when the playbook doesnt exist
* dont log errors when finding python interpreter
* tests: whoops, check for presence of correct image
* commit image even if the a-p execution failed
* fixups: installation, typos

# 0.2.0

Renamed to `ansible-bender`, the binary name was left intact.

## Features

 * Failed builds are commited as `-failed`.
 * Added command `list-builds`.
 * Added command `get-logs`.
 * Added command `inspect`.
 * Implemented a caching mechanism:
   * Limitation of caching are file tasks: ansible can't detect that a file wasn't changed and reports it changed.
     This means that ab is not able to load such result from cache.
   * Caching can be controled by a tag `dont-cache` which you can put into a task.
 * You can disable layering either by build's option `--no-cache` or adding a tag `stop-Layering` to a task.


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

