.. _dcos-vagrant_cli:

Vagrant
=======

The :ref:`dcos-vagrant-cli:minidcos vagrant` CLI allows you to create, manage and destroy open source DC/OS and DC/OS Enterprise clusters on Vagrant VMs.

A typical CLI workflow for open source DC/OS may look like the following.
Install the CLI (see :doc:`install-cli`),  then create and manage a cluster:

.. prompt:: bash $,# auto
   :substitutions:

   # Fix issues shown by minidcos vagrant doctor
   $ minidcos vagrant doctor
   $ minidcos vagrant create ./dcos_generate_config.sh --agents 0
   default
   $ minidcos vagrant wait
   $ minidcos vagrant run --test-env --sync-dir /path/to/dcos/checkout pytest -k test_tls
   ...
   # Get onto a node
   $ minidcos vagrant run bash
   [master-0]# exit
   $ minidcos vagrant destroy

Each of these and more are described in detail below.

.. contents::
   :local:

.. include:: vagrant-backend-requirements.rst

Creating a Cluster
------------------

To create a cluster you first need to download a DC/OS installer.

This can be done via `the releases page <https://dcos.io/releases/>`__ or with the :ref:`dcos-vagrant-cli:download-installer` command.

`DC/OS Enterprise <https://d2iq.com/products/dcos>`__ is also supported.
Ask your sales representative for installers.

Creating a cluster is possible with the :ref:`dcos-vagrant-cli:create` command.
This command allows you to customize the cluster in many ways.

The command returns when the DC/OS installation process has started.
To wait until DC/OS has finished installing, use the :ref:`dcos-vagrant-cli:wait` command.

To use this cluster, it is useful to find details using the :ref:`dcos-vagrant-cli:inspect` command.

DC/OS Enterprise
~~~~~~~~~~~~~~~~

There are multiple DC/OS Enterprise-only features available in :ref:`dcos-vagrant-cli:create`.

The only extra requirement is to give a valid license key, for DC/OS 1.11+.
See :ref:`dcos-vagrant-cli:create` for details on how to provide a license key.

Ask your sales representative for DC/OS Enterprise installers.

For, example, run the following to create a DC/OS Enterprise cluster in strict mode:

.. prompt:: bash $,# auto
   :substitutions:

   $ minidcos vagrant create /path/to/dcos_generate_config.ee.sh \
        --license-key /path/to/license.txt \
        --security-mode strict

The command returns when the DC/OS installation process has started.
To wait until DC/OS has finished installing, use the :ref:`dcos-vagrant-cli:wait` command.

See :ref:`dcos-vagrant-cli:create` for details on this command and its options.

Cluster IDs
-----------

Clusters have unique IDs.
Multiple commands take ``--cluster-id`` options.
Specify a cluster ID in :ref:`dcos-vagrant-cli:create`, and then use it in other commands.
Any command which takes a ``--cluster-id`` option defaults to using "default" if no cluster ID is given.

Running commands on Cluster Nodes
---------------------------------

It is possible to run commands on a cluster node in multiple ways.
These include using :ref:`dcos-vagrant-cli:run` and ``ssh``.

Running commands on a cluster node using :ref:`dcos-vagrant-cli:run`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to run the following to run a command on an arbitrary master node.

.. prompt:: bash $,# auto
   :substitutions:

   $ minidcos vagrant run systemctl list-units

See :ref:`dcos-vagrant-cli:run` for more information on this command.

Running commands on a cluster node using ``ssh``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One SSH key allows access to all nodes in the cluster.
See this SSH key's path and the IP addresses of nodes using :ref:`dcos-vagrant-cli:inspect`.

Getting on to a Cluster Node
----------------------------

Sometimes it is useful to get onto a cluster node.
To do this, you can use any of the ways of :ref:`running-commands`.

For example, to use :ref:`dcos-vagrant-cli:run` to run ``bash`` to get on to an arbitrary master node:

.. prompt:: bash $,# auto
   :substitutions:

   $ minidcos vagrant run bash

Destroying Clusters
-------------------

There are two commands which can be used to destroy clusters.
These are :ref:`dcos-vagrant-cli:destroy` and :ref:`dcos-vagrant-cli:destroy-list`.

Either destroy a cluster with :ref:`dcos-vagrant-cli:destroy`:

.. prompt:: bash $,# auto
   :substitutions:

   $ minidcos vagrant destroy
   default
   $ minidcos vagrant destroy --cluster-id pr_4033_strict
   pr_4033_strict

or use :ref:`dcos-vagrant-cli:destroy-list` to destroy multiple clusters:

.. prompt:: bash $,# auto
   :substitutions:

   $ minidcos vagrant destroy-list pr_4033_strict pr_4019_permissive
   pr_4033_strict
   pr_4019_permissive

To destroy all clusters, run the following command:

.. prompt:: bash $,# auto
   :substitutions:

   $ minidcos vagrant destroy-list $(dcos-vagrant list)
   pr_4033_strict
   pr_4019_permissive

Running Integration Tests
-------------------------

The :ref:`dcos-vagrant-cli:run` command is useful for running integration tests.

To run integration tests which are developed in the a DC/OS checkout at :file:`/path/to/dcos`, you can use the following workflow:

.. prompt:: bash $,# auto
   :substitutions:

   $ minidcos vagrant create ./dcos_generate_config.sh
   $ minidcos vagrant wait
   $ minidcos vagrant run --test-env --sync-dir /path/to/dcos/checkout pytest -k test_tls.py

There are multiple options and shortcuts for using these commands.
See :ref:`dcos-vagrant-cli:run` for more information on this command.

Viewing the Web UI
------------------

To view the web UI of your cluster, use the :ref:`dcos-vagrant-cli:web` command.
To see the web UI URL of your cluster, use the :ref:`dcos-vagrant-cli:inspect` command.

Before viewing the UI, you may first need to `configure your browser to trust your DC/OS CA <https://docs.d2iq.com/mesosphere/dcos/2.1/security/ent/tls-ssl/ca-trust-browser/>`_, or choose to override the browser protection.

Using a Custom CA Certificate
-----------------------------

On DC/OS Enterprise clusters, it is possible to use a custom CA certificate.
See `the Custom CA certificate documentation <https://docs.d2iq.com/mesosphere/dcos/2.1/security/ent/tls-ssl/ca-custom/>`_ for details.
It is possible to use :ref:`dcos-vagrant-cli:create` to create a cluster with a custom CA certificate.

#. Create or obtain the necessary files:

   :file:`dcos-ca-certificate.crt`, :file:`dcos-ca-certificate-key.key`, and :file:`dcos-ca-certificate-chain.crt`.

#. Put the above-mentioned files into a directory, e.g. :file:`/path/to/genconf/`.

#. Create a file containing the "extra" configuration.

   :ref:`dcos-vagrant-cli:create` takes an ``--extra-config`` option.
   This adds the contents of the specified YAML file to a minimal DC/OS configuration.

   Create a file with the following contents:

   .. code:: yaml

      ca_certificate_path: genconf/dcos-ca-certificate.crt
      ca_certificate_key_path: genconf/dcos-ca-certificate-key.key
      ca_certificate_chain_path: genconf/dcos-ca-certificate-chain.crt

#. Create a cluster.

   .. prompt:: bash $,# auto
      :substitutions:

      $ minidcos vagrant create \
          /path/to/dcos_generate_config.ee.sh \
          --variant enterprise \
          --genconf-dir /path/to/genconf/ \
          --copy-to-master /path/to/genconf/dcos-ca-certificate-key.key:/var/lib/dcos/pki/tls/CA/private/custom_ca.key \
          --license-key /path/to/license.txt \
          --extra-config config.yml

#. Verify that everything has worked.

   See `Verify installation <https://docs.d2iq.com/mesosphere/dcos/2.1/security/ent/tls-ssl/ca-custom/#verify-installation>`_ for steps to verify that the DC/OS Enterprise cluster was installed properly with the custom CA certificate.

CLI Reference
-------------

.. click:: dcos_e2e_cli:dcos_vagrant
  :prog: minidcos vagrant
  :show-nested:
