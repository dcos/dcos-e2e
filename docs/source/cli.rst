Command Line Interface
======================

The CLI allows you to create, manage and destroy open source DC/OS and DC/OS Enterprise clusters on Docker nodes.

An typical CLI workflow may look like this:

.. code-block:: console

   $ dcos-docker create /tmp/dcos_generate_config.sh --agents 0 --cluster-id default
   default
   $ dcos-docker create /tmp/dcos_generate_config.sh --agents 5
   921214100
   $ dcos-docker wait
   $ dcos-docker run --sync-dir . pytest -k test_tls
   ...
   $ dcos-docker destroy $(dcos-docker list)

Each of these and more are described in detail below.

.. contents::
   :local:

.. include:: docker-backend-requirements.rst

.. include:: installation.rst

Creating a Cluster
------------------

Creating a cluster is possible with the ``dcos-docker create`` command.
This command allows you to customize the cluster in many ways.

See :ref:`the dcos-docker create reference <dcos-docker-create>` for details on this command and its options.

The command returns when the DC/OS installation process has started.
To wait until DC/OS has finished installing, use the :ref:`the dcos-docker wait <dcos-docker-wait>` command.

To use this cluster, it is useful to find details using the :ref:`the dcos-docker inspect <dcos-docker-inspect>` command.

DC/OS Enterprise
~~~~~~~~~~~~~~~~

There are multiple DC/OS Enterprise-only features available in :ref:`dcos-docker-create`.

The only extra requirement is to give a valid license key.
See :ref:`the dcos-docker create reference <dcos-docker-create>` for details on how to provide a license key.

"default" Cluster ID
--------------------

It can become tedious repeatedly typing the cluster ID, particularly if you only have one cluster.
As a convenience, any command which takes a ``cluster-id`` option,
apart from ``create``,
defaults to using "default" if no cluster ID is given.

This means that you can use ``--cluster-id=default`` and then use ``dcos-docker wait`` with no arguments to wait for the ``default`` cluster.

Getting on to a Cluster Node
----------------------------

Sometimes it is useful to get onto a cluster node.
As the nodes are all Docker containers, it is possible to use ``docker exec``.

To find the details of the nodes, use ``dcos-docker inspect --cluster-id <your-cluster-id>``.
Alternatively, use the ``--env`` flag to output commands to be evaluated as such:

.. code-block:: console

   $ eval $(dcos-docker inspect --cluster-id example --env)
   $ docker exec -it $MASTER_0 /bin/bash
   [root@dcos-e2e-5253252]# exit
   $

Which environment variables are available depends on the size of your cluster.

Another option is to run the following to get on to a random master node:

.. code-block:: console

   $ dcos-docker run --cluster-id example bash

However, it is often not necessary to get on to a cluster node.
A shortcut is instead to run a command like the following:

.. code-block:: console

   $ dcos-docker run systemctl list-units

This is run on a random master node.
See :ref:`the dcos-docker run reference <dcos-docker-run>` for more information on this command.

Viewing Debug Information
-------------------------

The CLI is quiet by default.
To see more information, use ``-v`` or ``-vv`` after ``dcos-docker``.

Running Integration Tests
-------------------------

The ``dcos-docker run`` command is useful for running integration tests.

To run integration tests which are developed in the a DC/OS checkout at ``/path/to/dcos``, you can use the following workflow:

.. code-block:: console

   $ dcos-docker create /tmp/dcos_generate_config.ee.sh --cluster-id default
   $ dcos-docker wait
   $ dcos-docker run --sync /path/to/dcos pytest -k test_tls.py

There are multiple options and shortcuts for using these commands.
See :ref:`the dcos-docker run reference <dcos-docker-run>` for more information on this command.

Viewing the Web UI
------------------

To view the web UI of your cluster, use the :ref:`dcos-docker-web` command.
If you instead want to view the web UI URL of your cluster, use the :ref:`dcos-docker-inspect` command.

Before viewing the UI, you may first need to `configure your browser to trust your DC/OS CA <https://docs.mesosphere.com/1.11/security/ent/tls-ssl/ca-trust-browser/>`_, or choose to override the browser protection.

CLI Reference
-------------

.. click:: cli:dcos_docker
  :prog: dcos-docker

.. _dcos-docker-create:

.. click:: cli:create
  :prog: dcos-docker create

.. click:: cli:list_clusters
  :prog: dcos-docker list

.. _dcos-docker-wait:

.. click:: cli:wait
  :prog: dcos-docker wait

.. _dcos-docker-run:

.. click:: cli:run
  :prog: dcos-docker run

.. _dcos-docker-inspect:

.. click:: cli:inspect_cluster
  :prog: dcos-docker inspect

.. click:: cli:sync_code
  :prog: dcos-docker sync

.. click:: cli:destroy
  :prog: dcos-docker destroy

.. _dcos-docker-doctor:

.. click:: cli:doctor
  :prog: dcos-docker doctor

.. _dcos-docker-web:

.. click:: cli:web
  :prog: dcos-docker web
