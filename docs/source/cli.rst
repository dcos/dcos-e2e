Command Line Interface
======================

The CLI allows you to create, manage and destroy open source DC/OS and DC/OS Enterprise clusters on Docker nodes.

A typical CLI workflow for open source DC/OS may look like this:

.. code-block:: console

   $ dcos-docker create /tmp/dcos_generate_config.sh --agents 0 --cluster-id default
   default
   # Without specifying a cluster ID for ``wait`` and ``run``, ``default``
   # is automatically used.
   $ dcos-docker wait
   $ dcos-docker run --sync-dir /path/to/dcos/checkout pytest -k test_tls
   ...
   $ dcos-docker destroy

Each of these and more are described in detail below.

.. contents::
   :local:

.. include:: docker-backend-requirements.rst

.. include:: installation.rst

Creating a Cluster
------------------

Creating a cluster is possible with the ``dcos-docker create`` command.
This command allows you to customize the cluster in many ways.

See :ref:`the dcos-docker create reference <dcos-docker-create>` for details on this command and its options.

The command returns when the DC/OS installation process has started.
To wait until DC/OS has finished installing, use the :ref:`the dcos-docker wait <dcos-docker-wait>` command.

To use this cluster, it is useful to find details using the :ref:`the dcos-docker inspect <dcos-docker-inspect>` command.

DC/OS Enterprise
~~~~~~~~~~~~~~~~

There are multiple DC/OS Enterprise-only features available in :ref:`dcos-docker-create`.

The only extra requirement is to give a valid license key, for DC/OS 1.11+.
See :ref:`the dcos-docker create reference <dcos-docker-create>` for details on how to provide a license key.

For, example, run the following to create a DC/OS Enterprise cluster in strict mode:

.. code-block:: console

   $ dcos-docker create /path/to/dcos_generate_config.ee.sh \
        --license-key /path/to/license.txt \
        --security-mode strict \
        --cluster-id default

"default" Cluster ID
--------------------

It can become tedious repeatedly typing the cluster ID, particularly if you only have one cluster.
As a convenience, any command which takes a ``cluster-id`` option,
apart from ``create``,
defaults to using "default" if no cluster ID is given.

This means that you can use ``--cluster-id=default`` and then use ``dcos-docker wait`` with no arguments to wait for the ``default`` cluster.

Getting on to a Cluster Node
----------------------------

Sometimes it is useful to get onto a cluster node.
As the nodes are all Docker containers, it is possible to use ``docker exec``.

To find the details of the nodes, use ``dcos-docker inspect --cluster-id <your-cluster-id>``.
Alternatively, use the ``--env`` flag to output commands to be evaluated as such:

.. code-block:: console

   $ eval $(dcos-docker inspect --cluster-id example --env)
   $ docker exec -it $MASTER_0 /bin/bash
   [root@dcos-e2e-5253252]# exit
   $

Which environment variables are available depends on the size of your cluster.

Another option is to run the following to get on to a random master node:

.. code-block:: console

   $ dcos-docker run --cluster-id example bash

However, it is often not necessary to get on to a cluster node.
A shortcut is instead to run a command like the following:

.. code-block:: console

   $ dcos-docker run systemctl list-units

This is run on a random master node.
See :ref:`the dcos-docker run reference <dcos-docker-run>` for more information on this command.

Destroying Clusters
-------------------

There are two commands which can be used to destroy clusters.
These are :ref:`dcos-docker-destroy` and :ref:`dcos-docker-destroy-list`.

Either destroy a cluster with :ref:`dcos-docker-destroy`:

.. code-block:: console

   $ dcos-docker destroy
   default
   $ dcos-docker destroy pr_4033_strict
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

Viewing Debug Information
-------------------------

The CLI is quiet by default.
To see more information, use ``-v`` or ``-vv`` after ``dcos-docker``.

Running Integration Tests
-------------------------

The ``dcos-docker run`` command is useful for running integration tests.

To run integration tests which are developed in the a DC/OS checkout at ``/path/to/dcos``, you can use the following workflow:

.. code-block:: console

   $ dcos-docker create /tmp/dcos_generate_config.ee.sh --cluster-id default
   $ dcos-docker wait
   $ dcos-docker run --sync /path/to/dcos pytest -k test_tls.py

There are multiple options and shortcuts for using these commands.
See :ref:`the dcos-docker run reference <dcos-docker-run>` for more information on this command.

Viewing the Web UI
------------------

To view the web UI of your cluster, use the :ref:`dcos-docker-web` command.
If you instead want to view the web UI URL of your cluster, use the :ref:`dcos-docker-inspect` command.

Before viewing the UI, you may first need to `configure your browser to trust your DC/OS CA <https://docs.mesosphere.com/1.11/security/ent/tls-ssl/ca-trust-browser/>`_, or choose to override the browser protection.

Using a Custom CA Certificate
-----------------------------

On DC/OS Enterprise clusters, it is possible to use a custom CA certificate.
See `the Custom CA certifiacte documentation <https://docs.mesosphere.com/1.11/security/ent/tls-ssl/ca-custom>`_ for details.
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
          --cluster-id default

#. Verify that everything has worked.

   See `Verify installation <https://docs.mesosphere.com/1.11/security/ent/tls-ssl/ca-custom/#verify-installation>`_ for steps to verify that the DC/OS Enterprise cluster was installed properly with the custom CA certificate.

CLI Reference
-------------

.. click:: cli:dcos_docker
  :prog: dcos-docker

.. _dcos-docker-create:

.. click:: cli:create
  :prog: dcos-docker create

.. click:: cli:list_clusters
  :prog: dcos-docker list

.. _dcos-docker-wait:

.. click:: cli:wait
  :prog: dcos-docker wait

.. _dcos-docker-run:

.. click:: cli:run
  :prog: dcos-docker run

.. _dcos-docker-inspect:

.. click:: cli:inspect_cluster
  :prog: dcos-docker inspect

.. click:: cli:sync_code
  :prog: dcos-docker sync

.. _dcos-docker-destroy:

.. click:: cli:destroy
  :prog: dcos-docker destroy

.. _dcos-docker-destroy-list:

.. click:: cli:destroy_list
  :prog: dcos-docker destroy-list

.. _dcos-docker-doctor:

.. click:: cli:doctor
  :prog: dcos-docker doctor

.. _dcos-docker-web:

.. click:: cli:web
  :prog: dcos-docker web
