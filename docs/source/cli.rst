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
   $ dcos_docker wait work
   $ dcos_docker run work pytest -k test_tls
   ...
   $ eval $(dcos_docker inspect --env)
   $ docker exec -it $MASTER_0 /bin/bash
   [root@dcos-e2e-5253252]# exit
   $ dcos_docker destroy $(dcos_docker list)

CLI Reference
-------------

.. click:: cli:create
  :prog: dcos_docker create

.. click:: cli:list_clusters
  :prog: dcos_docker list

.. click:: cli:wait
  :prog: dcos_docker wait

.. click:: cli:inspect_cluster
  :prog: dcos_docker inspect

.. click:: cli:destroy
  :prog: dcos_docker destroy
