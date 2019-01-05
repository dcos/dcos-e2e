Requirements
------------

Hardware
~~~~~~~~

A minimum of 2 GB of free memory is required per DC/OS node.

``ssh``
~~~~~~~

The ``ssh`` command must be available.

Vagrant by HashiCorp
~~~~~~~~~~~~~~~~~~~~

`Vagrant`_ must be installed.
This has been tested with:

* Vagrant 2.1.1
* Vagrant 2.1.2

Oracle VirtualBox
~~~~~~~~~~~~~~~~~

`VirtualBox`_ must be installed.
This has been tested with VirtualBox 5.1.18.

``vagrant-vbguest`` plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~

`vagrant-vbguest`_ must be installed.

``doctor`` command
~~~~~~~~~~~~~~~~~~

:ref:`dcos-vagrant-cli:minidcos vagrant` comes with the :ref:`dcos-vagrant-cli:doctor` command.
Run this command to check your system for common causes of problems.

.. _VirtualBox: https://www.virtualbox.org
.. _Vagrant: https://www.vagrantup.com
.. _vagrant-vbguest: https://github.com/dotless-de/vagrant-vbguest
