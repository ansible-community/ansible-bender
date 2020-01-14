.. ansible-bender documentation master file, created by
   sphinx-quickstart on Tue Jan 14 12:29:42 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ansible-bender
==============

Tool which bends containers using Ansible playbooks and turns them into container images. It has a pluggable builder selection — it is up to you to pick the tool which will be used to construct your container image. Right now the only supported builder is buildah. More to come in the future. Ansible-bender (ab) relies on Ansible connection plugins for performing builds.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   features.rst
   interface.rst
   installation.rst
   configuration.rst
   usage.rst
   cacheandlayer.rst
   contributing.rst



