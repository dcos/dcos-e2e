.. _dcos-vagrant_cli:

``dcos-vagrant`` CLI
====================

The ``dcos-vagrant`` CLI allows you to create, manage and destroy open source DC/OS and DC/OS Enterprise clusters on Docker nodes.

A typical CLI workflow for open source DC/OS may look like the following.
:ref:`Install the CLI <installation>`, then create, manage and destroy a cluster:

.. code-block:: console

   # Fix issues shown by dcos-vagrant doctor
   $ dcos-vagrant doctor
   $ dcos-vagrant create /tmp/dcos_generate_config.sh --agents 0
   default
   $ dcos-vagrant wait
   $ dcos-vagrant run --sync-dir /path/to/dcos/checkout pytest -k test_tls
   ...
   $ dcos-vagrant destroy

Each of these and more are described in detail below.

.. contents::
   :local:

.. include:: vagrant-backend-requirements.rst

.. include:: install-cli.rst

Creating a Cluster
------------------

To create a cluster you first need to download `a DC/OS release <https://dcos.io/releases/>`__.

`DC/OS Enterprise <https://mesosphere.com/product/>`__ is also supported.
Ask your sales representative for release artifacts.

Creating a cluster is possible with the ``dcos-vagrant create`` command.
This command allows you to customize the cluster in many ways.

See :ref:`the dcos-vagrant create reference <dcos-vagrant-create>` for details on this command and its options.

The command returns when the DC/OS installation process has started.
To wait until DC/OS has finished installing, use the :ref:`the dcos-vagrant wait <dcos-vagrant-wait>` command.

To use this cluster, it is useful to find details using the :ref:`the dcos-vagrant inspect <dcos-vagrant-inspect>` command.

DC/OS Enterprise
~~~~~~~~~~~~~~~~

There are multiple DC/OS Enterprise-only features available in :ref:`dcos-vagrant-create`.

The only extra requirement is to give a valid license key, for DC/OS 1.11+.
See :ref:`the dcos-vagrant create reference <dcos-vagrant-create>` for details on how to provide a license key.

Ask your sales representative for DC/OS Enterprise release artifacts.

For, example, run the following to create a DC/OS Enterprise cluster in strict mode:

.. code-block:: console

   $ dcos-vagrant create /path/to/dcos_generate_config.ee.sh \
        --license-key /path/to/license.txt \
        --security-mode strict

The command returns when the DC/OS installation process has started.
To wait until DC/OS has finished installing, use the :ref:`dcos-vagrant-wait` command.

See :ref:`the dcos-vagrant create reference <dcos-vagrant-create>` for details on this command and its options.

"default" Cluster ID
--------------------

It can become tedious repeatedly typing the cluster ID, particularly if you only have one cluster.
Any command which takes a ``cluster-id`` option defaults to using "default" if no cluster ID is given.
This means that you can use ``dcos-vagrant wait`` with no arguments to wait for the ``default`` cluster.

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

.. click:: cli.dcos_vagrant:run
  :prog: dcos-vagrant run

.. click:: cli.dcos_vagrant:inspect_cluster
  :prog: dcos-vagrant inspect

.. click:: cli.dcos_vagrant:sync_code
  :prog: dcos-vagrant sync

.. click:: cli.dcos_vagrant:wait
  :prog: dcos-vagrant wait

.. click:: cli.dcos_vagrant:web
  :prog: dcos-vagrant web
