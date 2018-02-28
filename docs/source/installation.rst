Installation
------------

DC/OS E2E consists of a :doc:`library` and a :doc:`cli`.

CLI macOS With Homebrew
~~~~~~~~~~~~~~~~~~~~~~~

To install the CLI on macOS, install `Homebrew`_.

Then install the latest stable version:

.. code:: sh

    brew install https://raw.githubusercontent.com/mesosphere/dcos-e2e/master/dcosdocker.rb

Or the latest ``master``:

Homebrew installs the dependencies for the latest released version and so installing ``master`` may not work.

.. code:: sh

    brew install --HEAD https://raw.githubusercontent.com/mesosphere/dcos-e2e/master/dcosdocker.rb


Library and CLI with Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Requires Python 3.5.2+.

Optionally replace ``master`` with a particular version of DC/OS E2E.
The latest release is |release|.

.. code:: sh

    pip install git+https://github.com/mesosphere/dcos-e2e.git@master


Windows
~~~~~~~

The only supported way to run DC/OS E2E on Windows is using Vagrant and VirtualBox.

- Ensure Virtualization and VT-X support is enabled in your PC's BIOS. Disable Hyper-V virtualisation. See https://www.howtogeek.com/213795/how-to-enable-intel-vt-x-in-your-computers-bios-or-uefi-firmware/
- Install `VirtualBox`_ and VirtualBox Extension Pack.
- Install `Vagrant`_.
- Install the Vagrant plugin for persistent disks:

.. code:: ps1

    vagrant plugin install vagrant-persistent-storage

- Optionally install the Vagrant plugins to cache package downloads and keep guest additions updates:

.. code:: ps1

        vagrant plugin install vagrant-cachier
        vagrant plugin install vagrant-vbguest

- Start Powershell and download the E2E ``Vagrantfile`` to a directory containing a DC/OS installer file:

.. code:: ps1

    ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/mesosphere/dcos-e2e/master/vagrant/Vagrantfile')) | Set-Content -LiteralPath Vagrantfile

- By default, the ``Vagrantfile`` installs DC/OS E2E from the most recent release at the time it is downloaded.  To use a different release, or any Git reference, set the environment variable ``DCOS_E2E_REF``:

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

The route will be removed on reboot. You can manually remove the route in PowerShell Run as Administrator using:

.. code:: ps1

    route delete 172.17.0.0


.. _Homebrew: https://brew.sh
.. _VirtualBox: https://www.virtualbox.org/wiki/Downloads
.. _Vagrant: https://www.vagrantup.com/downloads.html
