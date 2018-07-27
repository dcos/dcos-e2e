.. _dcos-docker_cli:

``dcos-docker`` CLI
===================

The ``dcos-docker`` CLI allows you to create, manage and destroy open source DC/OS and DC/OS Enterprise clusters on Docker nodes.

A typical CLI workflow for open source DC/OS may look like the following.
:ref:`Install the CLI <installation>`, then create, manage and destroy a cluster:

.. code-block:: console

   # Fix issues shown by dcos-docker doctor
   $ dcos-docker doctor
   $ dcos-docker download-artifact
   $ dcos-docker create /tmp/dcos_generate_config.sh --agents 0
   default
   $ dcos-docker wait
   $ dcos-docker run --sync-dir /path/to/dcos/checkout pytest -k test_tls
   ...
   # Get onto a node
   $ dcos-docker run bash
   $ dcos-docker destroy

Each of these and more are described in detail below.

.. contents::
   :local:

.. include:: docker-backend-requirements.rst

.. _installation:

.. include:: install-cli.rst


Creating a Cluster
------------------

To create a cluster you first need to download a DC/OS release artifact.

This can be done via `the releases page <https://dcos.io/releases/>`__ or with the :ref:`dcos-docker-download-artifact` command.

`DC/OS Enterprise <https://mesosphere.com/product/>`__ is also supported.
Ask your sales representative for release artifacts.

Creating a cluster is possible with the ``dcos-docker create`` command.
This command allows you to customize the cluster in many ways.

See :ref:`the dcos-docker create reference <dcos-docker-create>` for details on this command and its options.

The command returns when the DC/OS installation process has started.
To wait until DC/OS has finished installing, use the :ref:`the dcos-docker wait <dcos-docker-wait>` command.

To use this cluster, it is useful to find details using the :ref:`the dcos-docker inspect <dcos-docker-inspect>` command.

Using a custom Docker network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default DC/OS clusters are launched on the ``docker0`` network.

To launch a DC/OS cluster on a custom Docker network the network must first be created using the standard Docker CLI.
During :ref:`dcos-docker create <dcos-docker-create>` the command line option ``--network`` then takes the name of the Docker network as a parameter.

DC/OS nodes utilize an environment-specific ``ip-detect`` script to detect their current private IP address.
The default ``ip-detect`` script used by ``dcos-docker`` does only account for the ``docker0`` network case.
Therefore, in order for DC/OS to operate on a custom network a custom ``ip-detect`` script needs to be provided and put into the ``genconf`` directory before installing DC/OS.

The following IP detect script works for any custom Docker network:

.. code-block:: console

    #!/bin/bash -e
    if [ -f /sbin/ip ]; then
       IP_CMD=/sbin/ip
    else
       IP_CMD=/bin/ip
    fi
    $IP_CMD -4 -o addr show dev eth1 | awk '{split($4,a,"/");print a[1]}'

The :ref:`dcos-docker create <dcos-docker-create>` command supports overwriting the default ``genconf`` directory with the
contents of the directory supplied through the command line option ``--genconf-dir``.

.. code-block:: console

    # Create ip-detect as mentioned above
    $ docker network create custom-bridge
    $ mkdir custom-genconf
    $ mv ip-detect custom-genconf/ip-detect
    $ dcos-docker create /path/to/dcos_generate_config.sh
        --network custom-bridge
        --genconf-dir ./custom-genconf

The custom Docker network is not cleaned up by the ``dcos-docker`` CLI.

DC/OS Enterprise
~~~~~~~~~~~~~~~~

There are multiple DC/OS Enterprise-only features available in :ref:`dcos-docker-create`.

The only extra requirement is to give a valid license key, for DC/OS 1.11+.
See :ref:`the dcos-docker create reference <dcos-docker-create>` for details on how to provide a license key.

Ask your sales representative for DC/OS Enterprise release artifacts.

For, example, run the following to create a DC/OS Enterprise cluster in strict mode:

.. code-block:: console

   $ dcos-docker create /path/to/dcos_generate_config.ee.sh \
        --license-key /path/to/license.txt \
        --security-mode strict

The command returns when the DC/OS installation process has started.
To wait until DC/OS has finished installing, use the :ref:`dcos-docker-wait` command.

See :ref:`the dcos-docker create reference <dcos-docker-create>` for details on this command and its options.

"default" Cluster ID
--------------------

It can become tedious repeatedly typing the cluster ID, particularly if you only have one cluster.
Any command which takes a ``cluster-id`` option defaults to using "default" if no cluster ID is given.
This means that you can use ``dcos-docker wait`` with no arguments to wait for the ``default`` cluster.

.. _running-commands:

Running commands on Cluster Nodes
---------------------------------

It is possible to run commands on a cluster node in multiple ways.
These include using :ref:`dcos-docker-run`, ``docker exec`` and ``ssh``.

Running commands on a cluster node using :ref:`dcos-docker-run`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to run the following to run a command on an arbitrary master node.

.. code-block:: console

   $ dcos-docker run --cluster-id example systemctl list-units

See :ref:`the dcos-docker run reference <dcos-docker-run>` for more information on this command.
In particular see the ``--node`` option to choose a particular node to run the command on.

Running commands on a cluster node using ``docker exec``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each cluster node is a Docker container.
This means that you can use tools such as ``docker exec`` to run commands on nodes.
To do this, first choose the container ID of a node.
Use :ref:`dcos-docker-inspect` to see all node container IDs.

Alternatively, use the ``--env`` flag to output commands to be evaluated as such:

.. code-block:: console

   $ eval $(dcos-docker inspect --cluster-id example --env)
   $ docker exec -it $MASTER_0 systemctl list-units

Which environment variables are available depends on the size of your cluster.

Running commands on a cluster node using ``ssh``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One SSH key allows access to all nodes in the cluster.
See this SSH key's path and the IP addresses of nodes using :ref:`dcos-docker-inspect`.
The available SSH user is ``root``.

Getting on to a Cluster Node
----------------------------

Sometimes it is useful to get onto a cluster node.
To do this, you can use any of the ways of :ref:`running-commands`.

For example, to use :ref:`dcos-docker-run` to run ``bash`` to get on to an arbitrary master node:

.. code-block:: console

   $ dcos-docker run --cluster-id example bash

or, similarly, to use ``docker exec`` to get on to a specific node:

.. code-block:: console

   $ eval $(dcos-docker inspect --cluster-id example --env)
   $ docker exec -it $MASTER_0 bash

See :ref:`running-commands` for details on how to choose particular nodes.

Destroying Clusters
-------------------

There are two commands which can be used to destroy clusters.
These are :ref:`dcos-docker-destroy` and :ref:`dcos-docker-destroy-list`.

Either destroy a cluster with :ref:`dcos-docker-destroy`:

.. code-block:: console

   $ dcos-docker destroy
   default
   $ dcos-docker destroy --cluster-id pr_4033_strict
   pr_4033_strict

or use :ref:`dcos-docker-destroy-list` to destroy multiple clusters:

.. code-block:: console

   $ dcos-docker destroy-list pr_4033_strict pr_4019_permissive
   pr_4033_strict
   pr_4019_permissive

To destroy all clusters, run the following command:

.. code-block:: console

   $ dcos-docker destroy-list $(dcos-docker list)
   pr_4033_strict
   pr_4019_permissive

.. _running-integration-tests:

Running Integration Tests
-------------------------

The :ref:`dcos-docker-run` command is useful for running integration tests.

To run integration tests which are developed in the a DC/OS checkout at :file:`/path/to/dcos`, you can use the following workflow:

.. code-block:: console

   $ dcos-docker create /tmp/dcos_generate_config.ee.sh
   $ dcos-docker wait
   $ dcos-docker run --sync-dir /path/to/dcos/checkout pytest -k test_tls.py

There are multiple options and shortcuts for using these commands.
See :ref:`the dcos-docker run reference <dcos-docker-run>` for more information on this command.

Viewing the Web UI
------------------

To view the web UI of your cluster, use the :ref:`dcos-docker-web` command.
To see the web UI URL of your cluster, use the :ref:`dcos-docker-inspect` command.

Before viewing the UI, you may first need to `configure your browser to trust your DC/OS CA <https://docs.mesosphere.com/1.11/security/ent/tls-ssl/ca-trust-browser/>`_, or choose to override the browser protection.

macOS
~~~~~

On macOS, by default, viewing the web UI requires IP routing to be set up.
Use :ref:`dcos-docker-setup-mac-network` to set up IP routing.

The web UI is served by master nodes on port ``80``.
To view the web UI on macOS without setting up IP routing, use the ``--one-master-host-port-map`` option on the :ref:`dcos-docker-create` command to forward port ``80`` to your host.
For example:

.. code-block:: console

   $ dcos-docker create /tmp/dcos_generate_config.ee.sh --one-master-host-port-map 70:80
   $ dcos-docker wait
   $ open localhost:70

Using a Custom CA Certificate
-----------------------------

On DC/OS Enterprise clusters, it is possible to use a custom CA certificate.
See `the Custom CA certificate documentation <https://docs.mesosphere.com/1.11/security/ent/tls-ssl/ca-custom>`_ for details.
It is possible to use :ref:`dcos-docker-create` to create a cluster with a custom CA certificate.

#. Create or obtain the necessary files:

   :file:`dcos-ca-certificate.crt`, :file:`dcos-ca-certificate-key.key`, and :file:`dcos-ca-certificate-chain.crt`.

#. Put the above-mentioned files, into a directory, e.g. :file:`/path/to/genconf/`.

#. Create a file containing the "extra" configuration.

   :ref:`dcos-docker-create` takes an ``--extra-config`` option.
   This adds the contents of the specified YAML file to a minimal DC/OS configuration.

   Create a file with the following contents:

   .. code:: yaml

      ca_certificate_path: genconf/dcos-ca-certificate.crt
      ca_certificate_key_path: genconf/dcos-ca-certificate-key.key
      ca_certificate_chain_path: genconf/dcos-ca-certificate-chain.crt

#. Create a cluster.

   .. code:: console

      dcos-docker create \
          /path/to/dcos_generate_config.ee.sh \
          --genconf-dir /path/to/genconf/ \
          --copy-to-master /path/to/genconf/dcos-ca-certificate-key.key:/var/lib/dcos/pki/tls/CA/private/custom_ca.key \
          --license-key /path/to/license.txt \
          --extra-config config.yml \

#. Verify that everything has worked.

   See `Verify installation <https://docs.mesosphere.com/1.11/security/ent/tls-ssl/ca-custom/#verify-installation>`_ for steps to verify that the DC/OS Enterprise cluster was installed properly with the custom CA certificate.

.. include:: docker-backend-limitations.rst

CLI Reference
-------------

.. click:: cli:dcos_docker
  :prog: dcos-docker

.. _dcos-docker-create:

.. click:: cli.dcos_docker:create
  :prog: dcos-docker create

.. click:: cli.dcos_docker:list_clusters
  :prog: dcos-docker list

.. _dcos-docker-wait:

.. click:: cli.dcos_docker:wait
  :prog: dcos-docker wait

.. _dcos-docker-run:

.. click:: cli.dcos_docker:run
  :prog: dcos-docker run

.. _dcos-docker-inspect:

.. click:: cli.dcos_docker:inspect_cluster
  :prog: dcos-docker inspect

.. click:: cli.dcos_docker:sync_code
  :prog: dcos-docker sync

.. _dcos-docker-destroy:

.. click:: cli.dcos_docker:destroy
  :prog: dcos-docker destroy

.. _dcos-docker-destroy-list:

.. click:: cli.dcos_docker:destroy_list
  :prog: dcos-docker destroy-list

.. _dcos-docker-doctor:

.. click:: cli.dcos_docker:doctor
  :prog: dcos-docker doctor

.. _dcos-docker-web:

.. click:: cli.dcos_docker:web
  :prog: dcos-docker web

.. _dcos-docker-setup-mac-network:

.. click:: cli.dcos_docker:setup_mac_network
  :prog: dcos-docker setup-mac-network

.. _dcos-docker-destroy-mac-network:

.. click:: cli.dcos_docker:destroy_mac_network
  :prog: dcos-docker destroy-mac-network

.. _dcos-docker-download-artifact:

.. click:: cli.dcos_docker:download_artifact
  :prog: dcos-docker download-artifact
