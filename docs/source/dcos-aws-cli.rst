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
