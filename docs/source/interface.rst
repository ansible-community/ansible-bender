Interface
=========

Ansible-bender has these commands:


.. list-table::
   :widths: 25 25
   :header-rows: 1

   * - Command
     - Description
   * - ``Build``
     - Build a new container image using selected playbook
   * - ``list-builds``
     - List all builds
   * - ``get-logs``
     - Display build logs
   * - ``inspect``
     - Provide detailed metadata about the selected build
   * - ``push``
     - Push images you built to remote locations.
   * - ``clean``
     - Clean images from database which are no longer present on the disk.
   * - ``init``
     - Adds a template playbook with all the vars.
