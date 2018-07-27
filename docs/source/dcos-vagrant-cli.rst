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

To create a cluster you first need to download a DC/OS release artifact.

This can be done via `the releases page <https://dcos.io/releases/>`__ or with the :ref:`dcos-vagrant-download-artifact` command.

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

Running commands on Cluster Nodes
---------------------------------

It is possible to run commands on a cluster node in multiple ways.
These include using :ref:`dcos-vagrant-run` and ``ssh``.

Running commands on a cluster node using :ref:`dcos-vagrant-run`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to run the following to run a command on an arbitrary master node.

.. code-block:: console

   $ dcos-vagrant run --cluster-id example systemctl list-units

See :ref:`the dcos-vagrant run reference <dcos-vagrant-run>` for more information on this command.

Running commands on a cluster node using ``ssh``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One SSH key allows access to all nodes in the cluster.
See this SSH key's path and the IP addresses of nodes using :ref:`dcos-vagrant-inspect`.

Getting on to a Cluster Node
----------------------------

Sometimes it is useful to get onto a cluster node.
To do this, you can use any of the ways of :ref:`running-commands`.

For example, to use :ref:`dcos-vagrant-run` to run ``bash`` to get on to an arbitrary master node:

.. code-block:: console

   $ dcos-vagrant run --cluster-id example bash

Destroying Clusters
-------------------

There are two commands which can be used to destroy clusters.
These are :ref:`dcos-vagrant-destroy` and :ref:`dcos-vagrant-destroy-list`.

Either destroy a cluster with :ref:`dcos-vagrant-destroy`:

.. code-block:: console

   $ dcos-vagrant destroy
   default
   $ dcos-vagrant destroy --cluster-id pr_4033_strict
   pr_4033_strict

or use :ref:`dcos-vagrant-destroy-list` to destroy multiple clusters:

.. code-block:: console

   $ dcos-vagrant destroy-list pr_4033_strict pr_4019_permissive
   pr_4033_strict
   pr_4019_permissive

To destroy all clusters, run the following command:

.. code-block:: console

   $ dcos-vagrant destroy-list $(dcos-vagrant list)
   pr_4033_strict
   pr_4019_permissive

Running Integration Tests
-------------------------

The :ref:`dcos-vagrant-run` command is useful for running integration tests.

To run integration tests which are developed in the a DC/OS checkout at :file:`/path/to/dcos`, you can use the following workflow:

.. code-block:: console

   $ dcos-vagrant create /tmp/dcos_generate_config.ee.sh
   $ dcos-vagrant wait
   $ dcos-vagrant run --sync-dir /path/to/dcos/checkout pytest -k test_tls.py

There are multiple options and shortcuts for using these commands.
See :ref:`the dcos-vagrant run reference <dcos-vagrant-run>` for more information on this command.

Viewing the Web UI
------------------

To view the web UI of your cluster, use the :ref:`dcos-vagrant-web` command.
To see the web UI URL of your cluster, use the :ref:`dcos-vagrant-inspect` command.

Before viewing the UI, you may first need to `configure your browser to trust your DC/OS CA <https://docs.mesosphere.com/1.11/security/ent/tls-ssl/ca-trust-browser/>`_, or choose to override the browser protection.

CLI Reference
-------------

.. click:: cli:dcos_vagrant
  :prog: dcos-vagrant

.. _dcos-vagrant-create:

.. click:: cli.dcos_vagrant:create
  :prog: dcos-vagrant create

.. click:: cli.dcos_vagrant:list_clusters
  :prog: dcos-vagrant list

.. _dcos-vagrant-wait:

.. click:: cli.dcos_vagrant:wait
  :prog: dcos-vagrant wait

.. _dcos-vagrant-run:

.. click:: cli.dcos_vagrant:run
  :prog: dcos-vagrant run

.. _dcos-vagrant-inspect:

.. click:: cli.dcos_vagrant:inspect_cluster
  :prog: dcos-vagrant inspect

.. click:: cli.dcos_vagrant:sync_code
  :prog: dcos-vagrant sync

.. _dcos-vagrant-destroy:

.. click:: cli.dcos_vagrant:destroy
  :prog: dcos-vagrant destroy

.. _dcos-vagrant-destroy-list:

.. click:: cli.dcos_vagrant:destroy_list
  :prog: dcos-vagrant destroy-list

.. _dcos-vagrant-doctor:

.. click:: cli.dcos_vagrant:doctor
  :prog: dcos-vagrant doctor

.. _dcos-vagrant-web:

.. click:: cli.dcos_vagrant:web
  :prog: dcos-vagrant web

.. _dcos-vagrant-download-artifact:

.. click:: cli.dcos_vagrant:download_artifact
  :prog: dcos-vagrant download-artifact
