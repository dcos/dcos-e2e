Docker Backend
==============

The Docker backend is user to spin up clusters on Docker containers, where each container is a DC/OS node.

.. include:: docker-backend-requirements.rst

DC/OS Installation
------------------

:py:class:`~dcos_e2e.cluster.Cluster`\ s created by the Docker backend only support installing DC/OS via :py:meth:`~dcos_e2e.cluster.Cluster.install_dcos_from_path`.
:py:class:`~dcos_e2e.node.Node`\ s of :py:class:`~dcos_e2e.cluster.Cluster`\ s created by the Docker backend do not distinguish between :py:attr:`~dcos_e2e.node.Node.public_ip_address` and :py:attr:`~dcos_e2e.node.Node.private_ip_address`.

Windows
-------

The only supported way to use the Docker backend on Windows is using Vagrant and VirtualBox.

- Ensure Virtualization and VT-X support is enabled in your PC's BIOS.
  Disable Hyper-V virtualization.
  See https://www.howtogeek.com/213795/how-to-enable-intel-vt-x-in-your-computers-bios-or-uefi-firmware/.
- Install `VirtualBox`_ and VirtualBox Extension Pack.
- Install `Vagrant`_.
- Install the Vagrant plugin for persistent disks:

.. code:: ps1

    vagrant plugin install vagrant-persistent-storage

- Optionally install the Vagrant plugins to cache package downloads and keep guest additions updates:

.. code:: ps1

    vagrant plugin install vagrant-cachier
    vagrant plugin install vagrant-vbguest

- Start Powershell and download the DC/OS E2E ``Vagrantfile`` to a directory containing a DC/OS installer file:

.. code:: ps1

    ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/mesosphere/dcos-e2e/master/vagrant/Vagrantfile')) | Set-Content -LiteralPath Vagrantfile

- By default, the :file:`Vagrantfile` installs DC/OS E2E from the most recent release at the time it is downloaded.
  To use a different release, or any Git reference, set the environment variable ``DCOS_E2E_REF``:

.. code:: ps1

    $env:DCOS_E2E_REF = "master"

- Start the virtual machine and login:

.. code:: ps1

    vagrant up
    vagrant ssh

You can now run :doc:`cli` commands or use the :doc:`library`.

To connect to the cluster nodes from the Windows host (e.g. to use the DC/OS web interface), in PowerShell Run as Administrator, and add the Virtual Machine as a gateway:

.. code:: ps1

    route add 172.17.0.0 MASK 255.255.0.0 192.168.18.2

To shutdown, logout of the virtual machine shell, and destroy the virtual machine and disk:

.. code:: ps1

    vagrant destroy

The route will be removed on reboot.
You can manually remove the route in PowerShell Run as Administrator using:

.. code:: ps1

    route delete 172.17.0.0

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

.. _VirtualBox: https://www.virtualbox.org/wiki/Downloads
.. _Vagrant: https://www.vagrantup.com/downloads.html
