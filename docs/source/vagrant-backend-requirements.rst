Requirements
------------

Hardware
~~~~~~~~

A minimum of 2 GB of free memory is required per DC/OS node.

``ssh``
~~~~~~~

The ``ssh`` command must be available to use the :py:class:`~dcos_e2e.node.Transport.SSH` transport.

Vagrant
~~~~~~~

`Vagrant`_ must be installed.
This has been tested with:

* Vagrant 2.1.1
* Vagrant 2.1.2

VirtualBox
~~~~~~~~~~

`VirtualBox`_ must be installed.
This has been tested with VirtualBox 5.1.18.

``vagrant-vbguest``
~~~~~~~~~~~~~~~~~~~

`vagrant-vbguest`_ must be installed.

``dcos-vagrant doctor``
~~~~~~~~~~~~~~~~~~~~~~~

|project| comes with the :ref:`dcos-vagrant-doctor` command.
Run this command to check your system for common causes of problems.
