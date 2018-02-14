Command Line Interface
======================

DC/OS E2E provides a command line interface which includes many of the features of the library.
The CLI is limited to the Docker backend and it is intented for use in developing and experimenting with DC/OS.

It allows you to create, manage and destroy open source DC/OS and DC/OS Enterprise clusters.
Each cluster node is emulated by a Docker container.

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
