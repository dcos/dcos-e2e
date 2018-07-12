.. _vagrant_backend:

Vagrant Backend
===============

The Vagrant backend is used to spin up clusters on Vagrant virtual machines, where each virtual machine is a DC/OS node.

.. include:: vagrant-backend-requirements.rst

Reference
---------

.. autoclass:: dcos_e2e.backends.Vagrant

.. _VirtualBox: https://www.virtualbox.org
.. _Vagrant: https://www.vagrantup.com
.. _vagrant-vbguest: https://github.com/dotless-de/vagrant-vbguest
