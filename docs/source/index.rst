DC/OS E2E
=========

DC/OS E2E is a tool for spinning up and managing DC/OS clusters in test environments.

Installation
------------

Requires Python 3.5.2+.

Optionally replace ``master`` with a particular version of DC/OS E2E.
The latest release is |release|.

.. code:: sh

    pip install --process-dependency-links git+https://github.com/mesosphere/dcos-e2e.git@master

Getting Started
---------------

To create a DC/OS cluster, you need a backend.
Backends are customizable, but for now let's use a standard :doc:`Docker backend <docker-backend>`.

.. code:: python

    from dcos_e2e.backends import Docker
    from dcos_e2e.cluster import Cluster

    cluster = Cluster(cluster_backend=Docker())

It is also possible to use ``Cluster`` as a context manager.
Doing this means that the cluster is destroyed on exit.

To install DC/OS on a cluster, you need a DC/OS build artifact.
You can download one from `the DC/OS releases page <https://dcos.io/releases/>`_.
In this example we will use a open source DC/OS artifact downloaded to :file:`/tmp/dcos_generate_config.sh`.

.. code:: python

   from pathlib import Path

   oss_artifact = Path('/tmp/dcos_generate_config.sh')

There is much more that you can do with a cluster, and there are other ways to create a cluster.
See :doc:`the reference <cluster>` for more.

.. autoclass:: cluster.Cluster
   :members:
   :private-members:
   :special-members:

.. toctree::

   cluster
   node
   docker-backend
   enterprise
   contributing
   changelog

.. toctree::
   :hidden:

   modules
   dcos_e2e
