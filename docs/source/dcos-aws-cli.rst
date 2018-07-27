``dcos-aws`` CLI
================

The ``dcos-aws`` CLI allows you to create and manage open source DC/OS and DC/OS Enterprise clusters on AWS EC2 instances.

A typical CLI workflow for open source DC/OS may look like the following.
:ref:`Install the CLI <installation>`, then create and manage a cluster:

.. code-block:: console

   # Fix issues shown by dcos-aws doctor
   $ dcos-aws doctor
   $ dcos-aws create https://downloads.dcos.io/dcos/stable/dcos_generate_config.sh --agents 0
   default
   $ dcos-aws wait
   $ dcos-aws run --sync-dir /path/to/dcos/checkout pytest -k test_tls
   ...

Each of these and more are described in detail below.

.. contents::
   :local:

.. include:: aws-backend-requirements.rst

.. include:: install-cli.rst

Creating a Cluster
------------------

To create a cluster you first need the link to a DC/OS release artifact.

These can be found on `the releases page <https://dcos.io/releases/>`__.

`DC/OS Enterprise <https://mesosphere.com/product/>`__ is also supported.
Ask your sales representative for release artifacts.

Creating a cluster is possible with the ``dcos-vagrant create`` command.
This command allows you to customize the cluster in many ways.

See :ref:`the dcos-vagrant create reference <dcos-vagrant-create>` for details on this command and its options.

The command returns when the DC/OS installation process has started.
To wait until DC/OS has finished installing, use the :ref:`the dcos-vagrant wait <dcos-vagrant-wait>` command.

To use this cluster, it is useful to find details using the :ref:`the dcos-vagrant inspect <dcos-vagrant-inspect>` command.

CLI Reference
-------------

.. click:: cli:dcos_aws
  :prog: dcos-aws

.. click:: cli.dcos_aws:create
  :prog: dcos-aws create

.. _dcos-aws-doctor:

.. click:: cli.dcos_aws:doctor
  :prog: dcos-aws doctor

.. click:: cli.dcos_aws:list_clusters
  :prog: dcos-aws list

.. click:: cli.dcos_aws:run
  :prog: dcos-aws run

.. click:: cli.dcos_aws:inspect_cluster
  :prog: dcos-aws inspect

.. click:: cli.dcos_aws:sync_code
  :prog: dcos-aws sync

.. click:: cli.dcos_aws:wait
  :prog: dcos-aws wait

.. click:: cli.dcos_aws:web
  :prog: dcos-aws web
