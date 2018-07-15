.. _dcos-vagrant_cli:

``dcos-vagrant`` CLI
====================

The ``dcos-vagrant`` CLI allows you to create DC/OS clusters on Vagrant nodes.

.. contents::
   :local:

.. include:: vagrant-backend-requirements.rst

.. include:: install-cli.rst

CLI Reference
-------------

.. click:: cli:dcos_vagrant
  :prog: dcos-vagrant

.. _dcos-vagrant-create:

.. click:: cli.dcos_vagrant:create
  :prog: dcos-vagrant create

.. click:: cli.dcos_vagrant:LIST_CLUSTERS
  :prog: dcos-vagrant list

.. click:: cli.dcos_vagrant:destroy
  :prog: dcos-vagrant destroy

.. click:: cli.dcos_vagrant:destroy_list
  :prog: dcos-vagrant destroy-list

.. _dcos-vagrant-doctor:

.. click:: cli.dcos_vagrant:doctor
  :prog: dcos-vagrant doctor

.. click:: cli.dcos_docker:run
  :prog: dcos-docker run

.. click:: cli.dcos_vagrant:sync_code
  :prog: dcos-vagrant sync

.. click:: cli.dcos_vagrant:wait
  :prog: dcos-vagrant wait

.. click:: cli.dcos_vagrant:web
  :prog: dcos-vagrant web
