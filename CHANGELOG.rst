Changelog
=========

.. contents::

Next
----

2018.11.20.1
------------

- Allow multiple ``--sync-dir`` options to be given to ``run`` commands.

2018.11.20.0
------------

- Rename ``build_artifact`` and related variables to "installer".
- If syncing a DC/OS OSS repository to a DC/OS Enterprise cluster, only Open
  Source tests are synced.

2018.11.16.2
------------

2018.11.16.1
------------

- Backwards incompatible change: Changed CLI commands from ``dcos-docker`` to ``minidcos docker`` and alike.

2018.11.16.0
------------

- Add a ``dcos-docker doctor`` check for systemd.
- Add a progress bar for ``doctor`` commands.
- Log subprocess output unicode characters where possible.

2018.11.09.1
------------

- Backwards incompatible change: Change ``--no-test-env`` to ``--test-env`` on ``run`` commands, with the opposite default.

2018.11.09.0
------------

- Fix an issue which caused incompatible version errors between ``keyring`` and ``SecretStore`` dependencies.

2018.11.07.1
------------

2018.11.07.0
------------

- Add ``dcos-docker create-loopback-sidecar`` and ``dcos-docker destroy-loopback-sidecar`` commands to provide unformatted block devices to DC/OS.
- Add ``dcos-docker clean`` command to clean left over artifacts.
- Backwards incompatible change: Changed names of VPN containers on macOS.

2018.10.17.1
------------

2018.10.17.0
------------

- Fix an issue which stopped the SSH transport from working on CLIs.

2018.10.16.0
------------

- Remove ``log_output_live`` parameters on various functions in favor of new ``output`` options.
- ``Node.__init__``'s ``ssh_key_path`` parameter now expects a path to an SSH key file with specific permissions.
   See the documentation for this class for details.

2018.10.13.0
------------

2018.10.12.2
------------

2018.10.12.1
------------

2018.10.12.0
------------

- The ``docker-exec`` transport uses interactive mode only when running in a terminal.

2018.10.11.3
------------

2018.10.11.2
------------

2018.10.11.1
------------

2018.10.11.0
------------

- Show full path on ``download-artifact`` downloads.
- Default to downloading to the current directory for ``download-artifact`` downloads.
- Use a TTY on CLI run commands only if Stdin is a TTY.

2018.10.10.0
------------

- Fix issues which stopped pre-built Linux binaries from working.

2018.09.25.0
------------

- ``wait_for_dcos_oss`` and ``wait_for_dcos_ee`` now raise a custom ``DCOSTimeoutError`` if DC/OS has not started within one hour.

2018.09.06.0
------------

- The ``--variant`` option is now required for the ``dcos-aws`` CLI.
- Added the ability to install on Linux from a pre-built binary.
- Add the ability to do a release to a fork.

2018.08.31.0
------------

- Fix using macOS with no custom network.

2018.08.28.0
------------

- Support for CoreOS on the AWS backend.
- Fix an issue which prevented the Vagrant backend from working.

2018.08.22.0
------------

- Improve diagnostics when creating a Docker-backed cluster with no running Docker daemon.

2018.08.13.0
------------

- Add instructions for uninstalling |project-name|.

2018.08.03.0
------------

- Pin ``msrestazure`` pip dependency to specific version to avoid dependency conflict.

2018.07.31.0
------------

- Add a ``dcos-docker doctor`` check that relevant Docker images can be built.

2018.07.30.0
------------

- Add Red Hat Enterprise Linux 7.4 support to the AWS backend.

2018.07.27.0
------------

- Fix bug which meant that a user could not log in after ``dcos-docker wait`` on DC/OS Open Source clusters.
- Backwards incompatible change: Remove ``files_to_copy_to_installer`` from ``Cluster.__init__`` and add ``files_to_copy_to_genconf_dir`` as an argument to ``Cluster.install_dcos_from_path`` as well as ``Cluster.install_dcos_from_url``.
- Add ``files_to_copy_to_genconf_dir`` as an argument to ``Node.install_dcos_from_path`` and ``Node.install_dcos_from_url``.

2018.07.25.0
------------

- Add the capability of sending a directory to a ``Node`` via ``Node.send_file``.
- Add ``ip_detect_path`` to the each ``ClusterBackend`` as a property and to each install DC/OS function as a parameter.

2018.07.23.1
------------

2018.07.23.0
------------

- Add an initial ``dcos-aws`` CLI.

2018.07.22.1
------------

- Add ``dcos-docker download-artifact`` and ``dcos-vagrant download-artifact``.

2018.07.22.0
------------

- Add ``verbose`` option to multiple commands.

2018.07.16.0
------------

- Add ``virtualbox_description`` parameter to the ``Vagrant`` backend.
- Change the default transport for the Docker backend to ``DOCKER_EXEC``.

2018.07.15.0
------------

- Add a ``--one-master-host-port-map`` option to ``dcos-docker create``.

2018.07.10.0
------------

- Execute ``node-poststart`` checks in ``Cluster.wait_for_dcos`` and ``Cluster.wait_for_dcos_ee``.
- Add ``dcos-vagrant doctor`` checks.

2018.07.03.5
------------

- Add a ``--network`` option to the ``dcos-docker`` CLI.

2018.07.03.0
------------

- Add a ``dcos-vagrant`` CLI.

2018.07.01.0
------------

- Renamed Homebrew formula.
  To upgrade from a previous version, follow Homebrew's linking instructions after upgrade instructions.

2018.06.30.0
------------

- Add a ``Vagrant`` backend.

2018.06.28.2
------------

- Add a ``aws_instance_type`` parameter to the ``AWS`` backend.

2018.06.28.0
------------

- Compare ``Node`` objects based on the ``public_ip_address`` and ``private_ip_address``.

2018.06.26.0
------------

- Add a ``network`` parameter to the ``Docker`` backend.

2018.06.20.0
------------

- Add platform-independent DC/OS installation method from ``Path`` and URL on ``Node``.

2018.06.18.0
------------

- Add ``dcos-docker doctor`` check for a version conflict between systemd and Docker.
- Allow installing DC/OS by a URL on the Docker backend, and a cluster ``from_nodes``.

2018.06.14.1
------------

- Add ``Cluster.remove_node``.

2018.06.14.0
------------

- Add Ubuntu support to the Docker backend.
- Add ``aws_key_pair`` parameter to the AWS backend.
- Fix Linuxbrew installation on Ubuntu.

2018.06.12.1
------------

- Add a ``--wait`` flag to ``dcos-docker create`` to also wait for the cluster.

2018.06.12.0
------------

- ``dcos-docker create`` now creates clusters with the ``--cluster-id`` "default" by default.

2018.06.05.0
------------

- Change ``Node.default_ssh_user`` to ``Node.default_user``.
- Add a ``docker exec`` transport to ``Node`` operations.
- Add a ``--transport`` options to multiple ``dcos-docker`` commands.

2018.05.29.0
------------

- Do not pin ``setuptools`` to an exact version.

2018.05.24.2
------------

- Add ``--env`` option to ``dcos-docker run``.

2018.05.24.1
------------

- Make ``xfs_info`` available on nodes, meaning that preflight checks can be run on nodes with XFS.
- Fix ``dcos-docker doctor`` for cases where ``df`` produces very long results.

2018.05.21.0
------------

- Show a formatted error rather than a traceback if Docker cannot be connected to.
- Custom backends' must now implement a ``base_config`` method.
- Custom backends' installation methods must now take ``dcos_config`` rather than ``extra_config``.
- ``Cluster.install_dcos_from_url`` and ``Cluster.install_dcos_from_path`` now take ``dcos_config`` rather than ``extra_config``.

2018.05.17.0
------------

- Add a ``--variant`` option to ``dcos-docker create`` to speed up cluster creation.

2018.05.15.0
------------

- Add a ``test_host`` parameter to ``Cluster.run_integration_tests``.
- Add the ability to specify a node to use for ``dcos-docker run``.

2018.05.14.0
------------

- Show IP address in ``dcos-docker inspect``.

2018.05.10.0
------------

- Expose the SSH key location in ``dcos-docker inspect``.
- Make network created by ``setup-mac-network`` now survives restarts.

2018.05.02.0
------------

- Previously not all volumes were destroyed when destroying a cluster from the CLI or with the ``Docker`` backend.
  This has been resolved.
  To remove dangling volumes from previous versions, use ``docker volume prune``.
- Backwards incompatible change: ``mount`` parameters to ``Docker.__init__`` now take a ``list`` of ``docker.types.Mount``\s.
- Docker version 17.06 or later is now required for the CLI and for the ``Docker`` backend.

2018.04.30.2
------------

- Added ``dcos-docker destroy-mac-network`` command.
- Added a ``--force`` parameter to ``dcos-docker setup-mac-network`` to
  override files and containers.

2018.04.29.0
------------

- Added ``dcos-docker setup-mac-network`` command.

2018.04.25.0
------------

- Logs from dependencies are no longer emitted.
- The ``dcos-docker`` CLI now gives more feedback to let you know that things are happening.

2018.04.19.0
------------

- The AWS backend now supports DC/OS 1.9.
- The Docker backend now supports having custom mounts which apply to all nodes.
- Add ``custom-volume`` parameter (and similar for each node type) to ``dcos-docker create``.

2018.04.11.0
------------

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

- Add ``Vagrantfile`` to run |project-name| in a virtual machine.
- Add instructions for running |project-name| on Windows.
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
-  Repository moved to ``https://github.com/dcos/dcos-e2e``.
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

.. This document is included in the source tree as well as the Sphinx documentation.
.. We automatically define |project| in all Sphinx documentation.
.. Defining |project| twice causes an error.
.. We need it defined both in the source tree view (GitHub preview) and in Sphinx.
.. We therefore use |project-name| in this document.
.. |project-name| replace:: DC/OS E2E
