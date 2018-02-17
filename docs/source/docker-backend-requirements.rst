Requirements
------------

Docker
~~~~~~

Docker must be installed.

Plenty of memory must be given to Docker.
On Docker for Mac, this can be done from Docker > Preferences > Advanced.
This backend has been tested with a four node cluster with 9 GB memory given to Docker.

IP Routing Set Up for Docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On Docker for Mac this requires a tool such as `docker-mac-network <https://github.com/wojas/docker-mac-network>`__.

``ssh``
~~~~~~~

The ``ssh`` command must be available.

Operating System
~~~~~~~~~~~~~~~~

This tool has been tested on macOS with Docker for Mac and on Linux.

It is not expected that this tool will work out of the box with Windows.

If your operating system is not supported, it may be possible to use Vagrant, or another Linux virtual machine.

``dcos-docker doctor``
~~~~~~~~~~~~~~~~~~~~~~

DC/OS E2E comes with the :ref:`dcos-docker-doctor` command.
Run this command to check your system for common causes of problems.

This requires DC/OS E2E to be installed.
