Vagrant Backend
===============

The Vagrant backend is used to spin up clusters on Vagrant virtual machines, where each virtual machine is a DC/OS node.

Requirements
------------

Hardware
~~~~~~~~

A minimum of 2 GB of free memory is required per DC/OS node.

Vagrant
~~~~~~~

`Vagrant`_ must be installed.
This has been tested with Vagrant 2.1.1.

VirtualBox
~~~~~~~~~~

`VirtualBox`_ must be installed.
This has been tested with VirtualBox 5.1.18.

``vagrant-vbguest``
~~~~~~~~~~~~~~~~~~~

`vagrant-vbguest`_ must be installed.

Reference
---------

.. autoclass:: dcos_e2e.backends.Vagrant

.. _VirtualBox: https://www.virtualbox.org
.. _Vagrant: https://www.vagrantup.com
.. _vagrant-vbguest: https://github.com/dotless-de/vagrant-vbguest
