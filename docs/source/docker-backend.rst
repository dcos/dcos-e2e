Docker Backend
==============

The Docker backend is user to spin up clusters on Docker containers, where each container is a DC/OS node.

.. include:: docker-backend-requirements.rst

DC/OS Installation
------------------

:py:class:`~dcos_e2e.cluster.Cluster`\ s created by the Docker backend only support installing DC/OS via :py:meth:`~dcos_e2e.cluster.Cluster.install_dcos_from_path`.
:py:class:`~dcos_e2e.node.Node`\ s of :py:class:`~dcos_e2e.cluster.Cluster`\ s created by the Docker backend do not distinguish between :py:attr:`~dcos_e2e.node.Node.public_ip_address` and :py:attr:`~dcos_e2e.node.Node.private_ip_address`.

Troubleshooting
---------------

Cleaning Up and Fixing "Out of Space" Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If a test is interrupted, it can leave behind containers, volumes and files.
To remove these, run the following:

.. code:: sh

    docker stop $(docker ps -a -q --filter="name=dcos-e2e")
    docker rm --volumes $(docker ps -a -q --filter="name=dcos-e2e")
    docker volume prune --force

If this repository is available, run ``make clean``.

macOS File Sharing
~~~~~~~~~~~~~~~~~~

On macOS :file:`/tmp` is a symlink to :file:`/private/tmp`.
:file:`/tmp` is used by the harness.
Docker for Mac must be configured to allow :file:`/private` to be bind mounted into Docker containers.
This is the default.
See Docker > Preferences > File Sharing.

SELinux
~~~~~~~

Tests inherit the host’s environment.
Any tests that rely on SELinux being available require it be available on the host.

Clock sync errors
~~~~~~~~~~~~~~~~~

On various platforms, the clock can get out of sync between the host machine and Docker containers.
This is particularly problematic if using ``check_time: true`` in the DC/OS configuration.
To work around this, run ``docker run --rm --privileged alpine hwclock -s``.

Reference
---------

.. autoclass:: dcos_e2e.backends.Docker
