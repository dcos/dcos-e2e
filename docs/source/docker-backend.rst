Docker Backend
==============

The Docker backend is user to spin up clusters on Docker containers, where each container is a DC/OS node.

Requirements
------------

Docker
^^^^^^

Plenty of memory must be given to Docker.
On Docker for Mac, this can be done from Docker > Preferences > Advanced.
This backend has been tested with a four node cluster with 9 GB memory given to Docker.

IP routing set up for Docker
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On Docker for Mac this requires a tool such as `docker-mac-network <https://github.com/wojas/docker-mac-network>`__.

``ssh``
^^^^^^^

The ``ssh`` command must be available.

DC/OS Installation
------------------

``Cluster``\ s created by the Docker backend only support installing DC/OS via ``install_dcos_from_path``.
``Node``\ s of ``Cluster``\ s created by the Docker backend do not distinguish between ``public_ip_address`` and ``private_ip_address``.

Reference
---------

.. autoclass:: dcos_e2e.backends._docker.Docker

.. autoclass:: dcos_e2e.backends._docker.DockerCluster

.. autoclass:: dcos_e2e.distributions.Distribution
   :members:

.. autoclass:: dcos_e2e.docker_versions.DockerVersion
   :members:

.. autoclass:: dcos_e2e.docker_storage_drivers.DockerStorageDriver
   :members:
