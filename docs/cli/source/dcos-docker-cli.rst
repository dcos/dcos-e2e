.. _dcos-docker_cli:

Docker
======

The :ref:`dcos-docker-cli:minidcos docker` CLI allows you to create, manage and destroy open source DC/OS and DC/OS Enterprise clusters on Docker nodes.

A typical CLI workflow for open source DC/OS may look like the following.
Install the CLI (see :doc:`install-cli`),  then create and manage a cluster:

.. prompt:: bash $,# auto
   :substitutions:

   # Fix issues shown by minidcos docker doctor
   $ minidcos docker doctor
   $ minidcos docker download-installer
   $ minidcos docker create ./dcos_generate_config.sh --agents 0
   default
   $ minidcos docker wait
   $ minidcos docker run --test-env --sync-dir /path/to/dcos/checkout pytest -k test_tls
   ...
   # Get onto a node
   $ minidcos docker run bash
   [master-0]# exit
   $ minidcos docker destroy

Each of these and more are described in detail below.

.. contents::
   :local:

.. include:: docker-backend-requirements.rst

Creating a Cluster
------------------

To create a cluster you first need to download a DC/OS installer.

This can be done via `the releases page <https://dcos.io/releases/>`__ or with the :ref:`dcos-docker-cli:download-installer` command.

`DC/OS Enterprise <https://d2iq.com/products/dcos>`__ is also supported.
Ask your sales representative for installers.

Creating a cluster is possible with the :ref:`dcos-docker-cli:create` command.
This command allows you to customize the cluster in many ways.

The command returns when the DC/OS installation process has started.
To wait until DC/OS has finished installing, use the :ref:`dcos-docker-cli:wait` command.

To use this cluster, it is useful to find details using the :ref:`dcos-docker-cli:inspect` command.

Using a custom Docker network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default DC/OS clusters are launched on the ``docker0`` network.

To launch a DC/OS cluster on a custom Docker network the network must first be created using the standard Docker CLI.
During :ref:`dcos-docker-cli:create` the command line option ``--network`` then takes the name of the Docker network as a parameter.

DC/OS nodes utilize an environment-specific ``ip-detect`` script to detect their current private IP address.
The default ``ip-detect`` script used by :ref:`dcos-docker-cli:minidcos docker` does only account for the ``docker0`` network case.
Therefore, in order for DC/OS to operate on a custom network a custom ``ip-detect`` script needs to be provided and put into the ``genconf`` directory before installing DC/OS.

The following IP detect script works for any custom Docker network:

.. prompt:: bash $,# auto
   :substitutions:

    #!/bin/bash -e
    if [ -f /sbin/ip ]; then
       IP_CMD=/sbin/ip
    else
       IP_CMD=/bin/ip
    fi
    $IP_CMD -4 -o addr show dev eth1 | awk '{split($4,a,"/");print a[1]}'

The :ref:`dcos-docker-cli:create` command supports overwriting the default ``genconf`` directory with the
contents of the directory supplied through the command line option ``--genconf-dir``.

.. prompt:: bash $,# auto
   :substitutions:

    # Create ip-detect as mentioned above
    $ docker network create custom-bridge
    $ mkdir custom-genconf
    $ mv ip-detect custom-genconf/ip-detect
    $ minidcos docker create /path/to/dcos_generate_config.sh \
        --network custom-bridge \
        --genconf-dir ./custom-genconf

The custom Docker network is not cleaned up by the :ref:`dcos-docker-cli:minidcos docker` CLI.

DC/OS Enterprise
~~~~~~~~~~~~~~~~

There are multiple DC/OS Enterprise-only features available in :ref:`dcos-docker-cli:create`.

The only extra requirement is to give a valid license key, for DC/OS 1.11+.
See :ref:`dcos-docker-cli:create` for details on how to provide a license key.

Ask your sales representative for DC/OS Enterprise installers.

For, example, run the following to create a DC/OS Enterprise cluster in strict mode:

.. prompt:: bash $,# auto
   :substitutions:

   $ minidcos docker create /path/to/dcos_generate_config.ee.sh \
        --license-key /path/to/license.txt \
        --security-mode strict

The command returns when the DC/OS installation process has started.
To wait until DC/OS has finished installing, use the :ref:`dcos-docker-cli:wait` command.

See :ref:`dcos-docker-cli:create` for details on this command and its options.

Cluster IDs
-----------

Clusters have unique IDs.
Multiple commands take ``--cluster-id`` options.
Specify a cluster ID in :ref:`dcos-docker-cli:create`, and then use it in other commands.
Any command which takes a ``--cluster-id`` option defaults to using "default" if no cluster ID is given.

.. _running-commands:

Running commands on Cluster Nodes
---------------------------------

It is possible to run commands on a cluster node in multiple ways.
These include using :ref:`dcos-docker-cli:run`, ``docker exec`` and ``ssh``.

Running commands on a cluster node using :ref:`dcos-docker-cli:run`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to run the following to run a command on an arbitrary master node.

.. prompt:: bash $,# auto
   :substitutions:

   $ minidcos docker run systemctl list-units

See :ref:`dcos-docker-cli:run` for more information on this command.
In particular see the ``--node`` option to choose a particular node to run the command on.

Running commands on a cluster node using ``docker exec``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each cluster node is a Docker container.
This means that you can use tools such as ``docker exec`` to run commands on nodes.
To do this, first choose the container ID of a node.
Use :ref:`dcos-docker-cli:inspect` to see all node container IDs.

Running commands on a cluster node using ``ssh``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One SSH key allows access to all nodes in the cluster.
See this SSH key's path and the IP addresses of nodes using :ref:`dcos-docker-cli:inspect`.
The available SSH user is ``root``.

Getting on to a Cluster Node
----------------------------

Sometimes it is useful to get onto a cluster node.
To do this, you can use any of the ways of :ref:`running-commands`.

For example, to use :ref:`dcos-docker-cli:run` to run ``bash`` to get on to an arbitrary master node:

.. prompt:: bash $,# auto
   :substitutions:

   $ minidcos docker run example bash

or, similarly, to use ``docker exec`` to get on to a specific node:

.. prompt:: bash $,# auto
   :substitutions:

   $ eval $(minidcos docker inspect --env)
   $ docker exec -it $MASTER_0 bash

See :ref:`running-commands` for details on how to choose particular nodes.

Destroying Clusters
-------------------

There are two commands which can be used to destroy clusters.
These are :ref:`dcos-docker-cli:destroy` and :ref:`dcos-docker-cli:destroy-list`.

Either destroy a cluster with :ref:`dcos-docker-cli:destroy`:

.. prompt:: bash $,# auto
   :substitutions:

   $ minidcos docker destroy
   default
   $ minidcos docker destroy --cluster-id pr_4033_strict
   pr_4033_strict

or use :ref:`dcos-docker-cli:destroy-list` to destroy multiple clusters:

.. prompt:: bash $,# auto
   :substitutions:

   $ minidcos docker destroy-list pr_4033_strict pr_4019_permissive
   pr_4033_strict
   pr_4019_permissive

To destroy all clusters, run the following command:

.. prompt:: bash $,# auto
   :substitutions:

   $ minidcos docker destroy-list $(minidcos docker list)
   pr_4033_strict
   pr_4019_permissive

.. _running-integration-tests:

Running Integration Tests
-------------------------

The :ref:`dcos-docker-cli:run` command is useful for running integration tests.

To run integration tests which are developed in the a DC/OS checkout at :file:`/path/to/dcos`, you can use the following workflow:

.. prompt:: bash $,# auto
   :substitutions:

   $ minidcos docker create ./dcos_generate_config.sh
   $ minidcos docker wait
   $ minidcos docker run --test-env --sync-dir /path/to/dcos/checkout pytest -k test_tls.py

There are multiple options and shortcuts for using these commands.
See :ref:`dcos-docker-cli:run` for more information on this command.

Viewing the Web UI
------------------

To view the web UI of your cluster, use the :ref:`dcos-docker-cli:web` command.
To see the web UI URL of your cluster, use the :ref:`dcos-docker-cli:inspect` command.

Before viewing the UI, you may first need to `configure your browser to trust your DC/OS CA <https://docs.d2iq.com/mesosphere/dcos/2.1/security/ent/tls-ssl/ca-trust-browser/>`_, or choose to override the browser protection.

macOS
~~~~~

On macOS, by default, viewing the web UI requires IP routing to be set up.
Use :ref:`dcos-docker-cli:setup-mac-network` to set up IP routing.

The web UI is served by master nodes on port ``80``.
To view the web UI on macOS without setting up IP routing, use the ``--one-master-host-port-map`` option on the :ref:`dcos-docker-cli:create` command to forward port ``80`` to your host.
For example:

.. prompt:: bash $,# auto
   :substitutions:

   $ minidcos docker create ./dcos_generate_config.sh --one-master-host-port-map 70:80
   $ minidcos docker wait
   $ open localhost:70

Using a Custom CA Certificate
-----------------------------

On DC/OS Enterprise clusters, it is possible to use a custom CA certificate.
See `the Custom CA certificate documentation <https://docs.d2iq.com/mesosphere/dcos/2.1/security/ent/tls-ssl/ca-custom/>`_ for details.
It is possible to use :ref:`dcos-docker-cli:create` to create a cluster with a custom CA certificate.

#. Create or obtain the necessary files:

   :file:`dcos-ca-certificate.crt`, :file:`dcos-ca-certificate-key.key`, and :file:`dcos-ca-certificate-chain.crt`.

#. Put the above-mentioned files into a directory, e.g. :file:`/path/to/genconf/`.

#. Create a file containing the "extra" configuration.

   :ref:`dcos-docker-cli:create` takes an ``--extra-config`` option.
   This adds the contents of the specified YAML file to a minimal DC/OS configuration.

   Create a file with the following contents:

   .. code:: yaml

      ca_certificate_path: genconf/dcos-ca-certificate.crt
      ca_certificate_key_path: genconf/dcos-ca-certificate-key.key
      ca_certificate_chain_path: genconf/dcos-ca-certificate-chain.crt

#. Create a cluster.

   .. prompt:: bash $,# auto
      :substitutions:

      $ minidcos docker create \
          /path/to/dcos_generate_config.ee.sh \
          --variant enterprise \
          --genconf-dir /path/to/genconf/ \
          --copy-to-master /path/to/genconf/dcos-ca-certificate-key.key:/var/lib/dcos/pki/tls/CA/private/custom_ca.key \
          --license-key /path/to/license.txt \
          --extra-config config.yml

#. Verify that everything has worked.

   See `Verify installation <https://docs.d2iq.com/mesosphere/dcos/2.1/security/ent/tls-ssl/ca-custom/#verify-installation>`_ for steps to verify that the DC/OS Enterprise cluster was installed properly with the custom CA certificate.

Using a Loopback Sidecar
------------------------

The :ref:`dcos-docker-cli:create-loopback-sidecar` command can be used to create a
loopback sidecar.
This will provide all containers with a unformatted block device, mounted as a loopback device.
All containers have access to this loopback device.
Therefore, care must be taken that only a single container has write-access to it.

.. prompt:: bash $,# auto
   :substitutions:

   $ minidcos docker create-loopback-sidecar sidecar1
   /dev/loop0
   $ minidcos docker create /tmp/dcos_generate_config.sh
   $ minidcos docker wait
   $ minidcos docker destroy-loopback-sidecar sidecar1

Loopback sidecars can be listed with :ref:`dcos-docker-cli:list-loopback-sidecars`.
Loopback sidecars can be destroyed with :ref:`dcos-docker-cli:destroy-loopback-sidecar`.

.. include:: docker-backend-limitations.rst

CLI Reference
-------------

.. click:: dcos_e2e_cli:dcos_docker
  :prog: minidcos docker
  :show-nested:
