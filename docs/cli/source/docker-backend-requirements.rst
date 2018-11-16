Requirements
------------

Docker 17.06+
~~~~~~~~~~~~~

Docker version 17.06 or later must be installed.

Plenty of memory must be given to Docker.
On Docker for Mac, this can be done from Docker > Preferences > Advanced.
This backend has been tested with a four node cluster with 9 GB memory given to Docker.

IP Routing Set Up for Docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On macOS, hosts cannot connect to containers IP addresses by default.
This is required, for example, to access the web UI, to SSH to nodes and to use the DC/OS CLI.

Once the CLI is installed, run :ref:`dcos-docker-cli:setup-mac-network` to set up IP routing.

Without this, it is still possible to use some features.
Specify the ``--transport docker-exec`` and ``--skip-http-checks`` options where available.

``ssh``
~~~~~~~

The ``ssh`` command must be available to use the ``ssh`` transport options.

Operating System
~~~~~~~~~~~~~~~~

This tool has been tested on macOS with Docker for Mac and on Linux.

It has also been tested on Windows on Vagrant.

Windows
^^^^^^^

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

- Start Powershell and download the |project| ``Vagrantfile`` to a directory containing a DC/OS installer file:

.. code:: ps1

    ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/|github-owner|/|github-repository|/master/vagrant/Vagrantfile')) | Set-Content -LiteralPath Vagrantfile

- By default, the :file:`Vagrantfile` installs |project| from the most recent release at the time it is downloaded.
  To use a different release, or any Git reference, set the environment variable ``DCOS_E2E_REF``:

.. code:: ps1

    $env:DCOS_E2E_REF = "master"

- Start the virtual machine and login:

.. code:: ps1

    vagrant up
    vagrant ssh

You can now run :doc:`dcos-docker-cli` commands.

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

``doctor`` command
~~~~~~~~~~~~~~~~~~

:ref:`dcos-docker-cli:minidcos docker` comes with the :ref:`dcos-docker-cli:doctor` command.
Run this command to check your system for common causes of problems.

.. _VirtualBox: https://www.virtualbox.org/wiki/Downloads
.. _Vagrant: https://www.vagrantup.com/downloads.html
