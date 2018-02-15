Requirements
------------

``dcos_docker doctor``
~~~~~~~~~~~~~~~~~~~~~~

DC/OS E2E comes with the ``dcos_docker doctor`` command.
Run this command to check your system for common causes of problems.

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
