Changelog
=========

.. contents::

Next
----

- Add an AWS backend to the library.
- Add ability to control which labels are added to particular node types on the ``Docker`` backend.
- Add support for Ubuntu on the ``Docker`` backend.

2018.04.02.1
------------

- Add a new ``dcos-docker doctor`` check for suitable ``sed`` for DC/OS 1.9.
- Support ``cluster.run_integration_tests`` on DC/OS 1.9.

2018.04.02.0
------------

- Add support for DC/OS 1.9 on Linux hosts.
- ``dcos-docker doctor`` returns a status code of ``1`` if there are any errors.
- Add a new ``dcos-docker doctor`` check for free space in the Docker root directory.

2018.03.26.0
------------

- Add a ``dcos-docker doctor`` check that a supported storage driver is available.
- Fix error with using Docker version `v17.12.1-ce` inside Docker nodes.
- Fix race condition between installing DC/OS and SSH starting.
- Remove support for Ubuntu on the Docker backend.

2018.03.07.0
------------

- Fix public agents on DC/OS 1.10.
- Remove options to use Fedora and Debian in the ``Docker`` backend nodes.
- Fix the Ubuntu distribution on the ``Docker`` backend.
- Add support for Docker ``17.12.1-ce`` on nodes in the ``Docker`` backend.
- Exceptions in ``create`` in the CLI point towards the ``doctor`` command.
- Removed a race condition in the ``doctor`` command.
- ``dcos-docker run`` now exits with the return code of the command run.
- ``dcos-docker destroy-list`` is a new command and ``dcos-docker destroy`` now adheres to the common semantics of the CLI.

2018.02.28.0
------------

- Add ``Vagrantfile`` to run DC/OS E2E in a virtual machine.
- Add instructions for running DC/OS E2E on Windows.
- Allow relative paths for the build artifact.

2018.02.27.0
------------

-  Backwards incompatible change: Move ``default_ssh_user`` parameter from ``Cluster`` to ``Node``.
   The ``default_ssh_user`` is now used for ``Node.run``, ``Node.popen`` and ``Node.send_file`` if ``user`` is not supplied.

2018.02.23.0
------------

-  Add ``linux_distribution`` parameter to the ``Docker`` backend.
-  Add support for CoreOS in the ``Docker`` backend.
-  Add ``docker_version`` parameter to the ``Docker`` backend.
-  The fallback Docker storage driver for the ``Docker`` backend is now ``aufs``.
-  Add ``storage_driver`` parameter to the ``Docker`` backend.
-  Add ``docker_container_labels`` parameter to the ``Docker`` backend.
-  Logs are now less cluttered with escape characters.
-  Documentation is now on Read The Docs.
-  Add a Command Line Interface.
-  Vendor ``dcos_test_utils`` so ``--process-dependency-links`` is not needed.
-  Backwards incompatible change:
   ``Cluter``\'s ``files_to_copy_to_installer`` argument is now a ``List`` of ``Tuple``\s rather than a ``Dict``.
- Add a ``tty`` option to ``Node.run`` and ``Cluster.run_integration_tests``.

2018.01.25.0
------------

-  Backwards incompatible change:
   Change the default behavior of ``Node.run`` and ``Node.popen`` to quote arguments, unless a new ``shell`` parameter is ``True``.
   These methods now behave similarly to ``subprocess.run``.
-  Add custom string representation for ``Node`` object.
-  Bump ``dcos-test-utils`` for better diagnostics reports.

2018.01.22.0
------------

-  Expose the ``public_ip_address`` of the SSH connection and the ``private_ip_address`` of its DC/OS component on ``Node`` objects.
-  Bump ``dcos-test-utils`` for better diagnostics reports.

2017.12.11.0
------------

-  Replace the extended ``wait_for_dcos_ee`` timeout with a preceding ``dcos-diagnostics`` check.

2017.12.08.0
------------

-  Extend ``wait_for_dcos_ee`` timeout for waiting until the DC/OS CA cert can be fetched.

2017.11.29.0
------------

-  Backwards incompatible change:
   Introduce separate ``wait_for_dcos_oss`` and ``wait_for_dcos_ee`` methods.
   Both methods improve the boot process waiting time for the corresponding DC/OS version.
-  Backwards incompatible change: ``run_integration_tests`` now requires users to call ``wait_for_dcos_oss`` or ``wait_for_dcos_ee`` beforehand.

2017.11.21.0
------------

-  Remove ``ExistingCluster`` backend and replaced it with simpler ``Cluster.from_nodes`` method.
-  Simplified the default configuration for the Docker backend.
   Notably this no longer contains a default ``superuser_username`` or ``superuser_password_hash``.
-  Support ``custom_agent_mounts`` and ``custom_public_agent_mounts`` on the Docker backend.

2017.11.15.0
------------

-  Remove ``destroy_on_error`` and ``destroy_on_success`` from ``Cluster``.
   Instead, avoid using ``Cluster`` as a context manager to keep the cluster alive.

2017.11.14.0
------------

-  Backwards incompatible change: Rename ``DCOS_Docker`` backend to ``Docker`` backend.
-  Backwards incompatible change: Replace ``generate_config_path`` with ``build_artifact`` that can either be a ``Path`` or a HTTP(S) URL string.
   This allows for supporting installation methods that require build artifacts to be downloaded from a HTTP server.
-  Backwards incompatible change: Remove ``run_as_root``.
   Instead require a ``default_ssh_user`` for backends to ``run`` commands over SSH on any cluster ``Node`` created with this backend.
-  Backwards incompatible change: Split the DC/OS installation from the ClusterManager ``__init__`` procedure.
   This allows for installing DC/OS after ``Cluster`` creation, and therefore enables decoupling of transferring files ahead of the installation process.
-  Backwards incompatible change: Explicit distinction of installation methods by providing separate methods for ``install_dcos_from_path`` and ``install_dcos_from_url`` instead of inspecting the type of ``build_artifact``.
-  Backwards incompatible change: ``log_output_live`` is no longer an attribute of the ``Cluster`` class. It may now be passed separately as a parameter for each output-generating operation.

2017.11.02.0
------------

-  Added ``Node.send_file`` to allow files to be copied to nodes.
-  Added ``custom_master_mounts`` to the DC/OS Docker backend.
-  Backwards incompatible change: Removed ``files_to_copy_to_masters``.
   Instead, use ``custom_master_mounts`` or ``Node.send_file``.

2017.10.04.0
------------

-  Added Apache2 license.
-  Repository moved to ``https://github.com/mesosphere/dcos-e2e``.
-  Added ``run``, which is similar to ``run_as_root`` but takes a ``user`` argument.
-  Added ``popen``, which can be used for running commands asynchronously.

2017.08.11.0
------------

-  Fix bug where ``Node`` ``repr``\ s were put into environment variables rather than IP addresses.
   This prevented some integration tests from working.

2017.08.08.0
------------

-  Fixed issue which prevented ``files_to_copy_to_installer`` from working.

2017.08.05.0
------------

-  The Enterprise DC/OS integration tests now require environment variables describing the IP addresses of the cluster.
   Now passes these environment variables.

2017.06.23.0
------------

-  Wait for 5 minutes after diagnostics check.

2017.06.22.0
------------

-  Account for the name of ``3dt`` having changed to ``dcos-diagnostics``.

2017.06.21.1
------------

-  Support platforms where ``$HOME`` is set as ``/root``.
-  ``Cluster.wait_for_dcos`` now waits for CA cert to be available.

2017.06.21.0
------------

-  Add ability to specify a workspace.
-  Fixed issue with DC/OS Docker files not existing in the repository.

2017.06.20.0
------------

-  Vendor DC/OS Docker so a path is not needed.
-  If ``log_output_live`` is set to ``True`` for a ``Cluster``, logs are shown in ``wait_for_dcos``.

2017.06.19.0
------------

-  More storage efficient.
-  Removed need to tell ``Cluster`` whether a cluster is an enterprise cluster.
-  Removed need to tell ``Cluster`` the ``superuser_password``.
-  Added ability to set environment variables on remote nodes when running commands.

2017.06.15.0
------------

-  Initial release.
