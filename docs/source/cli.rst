Command Line Interface
======================

The CLI allows you to create, manage and destroy open source DC/OS and DC/OS Enterprise clusters on Docker nodes.

An typical CLI workflow may look like this:

.. code-block:: console

   $ dcos_docker create /tmp/dcos_generate_config.ee.sh --agents 0 --cluster-id default
   default
   $ dcos_docker create /tmp/dcos_generate_config.ee.sh --agents 5
   921214100
   $ dcos_docker wait
   $ dcos_docker run --sync . pytest -k test_tls
   ...
   $ dcos_docker destroy $(dcos_docker list)

Each of these and more are described in detail below.

.. contents::
   :local:

Requirements
------------

The CLI shares the :ref:`Docker backend requirements <docker-requirements>`.

.. include:: installation.rst

Creating a Cluster
------------------

Creating a cluster is possible with the ``dcos_docker create`` command.
This command allows you to customize the cluster in many ways.

See :ref:`the dcos_docker create reference <dcos_docker-create>` for details on this command and its options.

The command returns when the DC/OS installation process has started.
To wait until DC/OS has finished installing, use the :ref:`the dcos_docker wait <dcos_docker-wait>` command.

To use this cluster, it is useful to find details using the :ref:`the dcos_docker inspect <dcos_docker-inspect>` command.

"default" Cluster ID
--------------------

It can become tedious repeatedly typing the cluster ID, particularly if you only have one cluster.
As a convenience, any command which takes a ``cluster-id`` option,
apart from ``create``,
defaults to using "default" if no cluster ID is given.

This means that you can use ``--cluster-id=default`` and then use ``dcos_docker wait`` with no arguments to wait for the ``default`` cluster.

Getting on to a Cluster Node
----------------------------

Sometimes it is useful to get onto a cluster node.
As the nodes are all Docker containers, it is possible to use ``docker exec``.

To find the details of the nodes, use ``dcos_docker inspect --cluster-id <your-cluster-id>``.
Alternatively, use the ``--env`` flag to output commands to be evaluated as such:

.. code-block:: console

   $ eval $(dcos_docker inspect --cluster-id example --env)
   $ docker exec -it $MASTER_0 /bin/bash
   [root@dcos-e2e-5253252]# exit
   $

Which environment variables are available depends on the size of your cluster.

Another option is to run the following to get on to a random master node:

.. code-block:: console

   $ dcos_docker run --cluster-id example bash

However, it is often not necessary to get on to a cluster node.
A shortcut is instead to run a command like the following:

.. code-block:: console

   $ dcos_docker run systemctl list-units

This is run on a random master node.
See :ref:`the dcos_docker run reference <dcos_docker-run>` for more information on this command.

Viewing Debug Information
-------------------------

The CLI is quiet by default.
To see more information, use ``-v`` or ``-vv`` after ``dcos_docker``.

Running Integration Tests
-------------------------

The ``dcos_docker run`` command is useful for running integration tests.


To run integration tests which are developed in the a DC/OS checkout at ``/path/to/dcos``, you can use the following workflow:

.. code-block:: console

   $ dcos_docker create /tmp/dcos_generate_config.ee.sh --cluster-id default
   $ dcos_docker wait
   $ dcos_docker run --sync /path/to/dcos pytest -k test_tls.py

There are multiple options and shortcuts for using these commands.
See :ref:`the dcos_docker run reference <dcos_docker-run>` for more information on this command.

CLI Reference
-------------

.. _dcos_docker-create:

.. click:: cli:create
  :prog: dcos_docker create

.. click:: cli:list_clusters
  :prog: dcos_docker list

.. _dcos_docker-wait:

.. click:: cli:wait
  :prog: dcos_docker wait

.. _dcos_docker-run:

.. click:: cli:run
  :prog: dcos_docker run

.. _dcos_docker-inspect:

.. click:: cli:inspect_cluster
  :prog: dcos_docker inspect

.. click:: cli:sync_code
  :prog: dcos_docker sync

.. click:: cli:destroy
  :prog: dcos_docker destroy

.. click:: cli:doctor
  :prog: dcos_docker doctor
