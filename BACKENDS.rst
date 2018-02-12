Backends
========

DC/OS E2E has a pluggable backend system.
A backend is used as the ``cluster_backend`` parameter to the ``Cluster`` class.
These backend classes allow backend-specific configuration of the cluster.

.. contents::

``dcos_e2e.backend.Docker``
---------------------------

.. code:: python

    Docker(
        workspace_dir=None,
        custom_master_mounts=None,
        custom_agent_mounts=None,
        custom_public_agent_mounts=None,
        linux_distribution=dcos_e2e.distributions.Distributions,
        docker_version=dcos_e2e.docker_versions.DockerVersion,
        storage_driver=None,
        docker_container_labels=None,
    )


Parameters
~~~~~~~~~~

``workspace_dir``
^^^^^^^^^^^^^^^^^

The directory in which large temporary files will be created.
These files will be deleted at the end of a test run.
This is equivalent to ``dir`` in `TemporaryDirectory <https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryDirectory>`__.

``custom_master_mounts``, ``custom_agent_mounts``, ``custom_public_agent_mounts``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Mounts to add to node containers.
See ``volumes`` in `the ``docker-py`` documentation <http://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run>`__ for details.

``linux_distribution``
^^^^^^^^^^^^^^^^^^^^^^

Linux distribution to use. Currently only ``dcos_e2e.distributions.Distribution.CENTOS_7`` and ``dcos_e2e.distributions.Distribution.COREOS`` are supported.

``docker_version``
^^^^^^^^^^^^^^^^^^

The Docker version to use.
See ``list(dcos_e2e.docker_versions)`` for available versions.
Be sure to use a ``storage_driver`` which is compatible with the version of Docker that you are using.

``storage_driver``
^^^^^^^^^^^^^^^^^^

The Docker storage driver to use.
The storage driver is the host’s driver by default.
If this is not a supported driver, ``aufs`` is used.
See ``list(dcos_e2e.docker_storage_drivers)`` for available storage drivers.

On some platforms, Docker will fail to start up with certain storage drivers.

``docker_container_labels``
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Docker labels to add to the cluster node containers.
Akin to the dictionary option in `docker-py <http://docker-py.readthedocs.io/en/stable/containers.html>`__.

DC/OS Installation
~~~~~~~~~~~~~~~~~~

``Cluster``\ s created by the Docker backend only support installing DC/OS via ``install_dcos_from_path``.
``Node``\ s of ``Cluster``\ s created by the Docker backend do not distinguish between ``public_ip_address`` and ``private_ip_address``.

Troubleshooting
~~~~~~~~~~~~~~~

Cleaning Up and Fixing "Out of Space" Errors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If a test is interrupted, it can leave behind containers, volumes and files.
To remove these, run the following:

.. code:: sh

    docker stop $(docker ps -a -q --filter="name=dcos-e2e")
    docker rm --volumes $(docker ps -a -q --filter="name=dcos-e2e")
    docker volume prune --force

If this repository is available, run ``make clean``.

macOS File Sharing
^^^^^^^^^^^^^^^^^^

On macOS ``/tmp`` is a symlink to ``/private/tmp``.
``/tmp`` is used by the harness.
Docker for Mac must be configured to allow ``/private`` to be bind mounted into Docker containers.
This is the default.
See Docker > Preferences > File Sharing.

SELinux
^^^^^^^

Tests inherit the host’s environment.
Any tests that rely on SELinux being available require it be available on the host.

Clock sync errors
^^^^^^^^^^^^^^^^^

On various platforms, the clock can get out of sync between the host machine and Docker containers.
This is particularly problematic if using ``check_time: true`` in the DC/OS configuration.
To work around this, run ``docker run --rm --privileged alpine hwclock -s``.

Using existing nodes
--------------------

It is possible to use existing nodes on any platform with DC/OS E2E.

``Cluster.from_nodes(masters, agents, public_agents, default_ssh_user)``

Clusters created with this method cannot be destroyed by DC/OS E2E.
It is assumed that DC/OS is already up and running on the given nodes and installing DC/OS is not supported.
