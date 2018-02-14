Command Line Interface
======================

DC/OS E2E provides a command line interface which includes many of the features of the library.
The CLI is limited to the Docker backend and it is intented for use in developing and experimenting with DC/OS.

It allows you to create, manage and destroy open source DC/OS and DC/OS Enterprise clusters.
Each cluster node is emulated by a Docker container.

An typical CLI workflow may look like this:

.. code-block:: console

   $ dcos_docker create /tmp/dcos_generate_config.ee.sh --agents 0 --cluster-id work
   work
   $ dcos_docker create /tmp/dcos_generate_config.sh --agents 0
   9452525358324
   $ dcos_docker list
   work
   9452525358324
   $ dcos_docker wait --cluster-id work
   $ dcos_docker run --sync /path/to/dcos-enteprise --cluster-id work pytest -k test_tls
   ...
   $ dcos_docker destroy $(dcos_docker list)

Each of these commands is described in detail below.

Default Cluster Name
--------------------

It can become tedious repeatly typing the cluster ID, particularly if you only have one cluster.
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

CLI Reference
-------------

.. click:: cli:create
  :prog: dcos_docker create

.. click:: cli:list_clusters
  :prog: dcos_docker list

.. click:: cli:wait
  :prog: dcos_docker wait

.. click:: cli:run
  :prog: dcos_docker run

.. click:: cli:inspect_cluster
  :prog: dcos_docker inspect

.. click:: cli:sync_code
  :prog: dcos_docker sync

.. click:: cli:destroy
  :prog: dcos_docker destroy
