Cluster
=======

Using DC/OS E2E usually involves creating one or more ``Cluster``\s.
A cluster is created using a "backend", which might be Docker or a cloud provider for example.
It is also possible to point DC/OS E2E to existing nodes.
A ``Cluster`` object is then used to interact with the DC/OS cluster.

.. automethod:: dcos_e2e.cluster.Cluster.__init__

Choosing a Backend
------------------

At the time of writing the only backend which ships with DC/OS E2E is :doc:`the Docker backend <docker-backend>`.
It is also possible to :doc:`create your own backend <custom-backend>`.

Creating a Cluster from Existing Nodes
--------------------------------------

It is possible to create a ``Cluster`` from existing nodes.
Clusters created with this method cannot be destroyed by DC/OS E2E.
It is assumed that DC/OS is already up and running on the given nodes and installing DC/OS is not supported.

.. automethod:: dcos_e2e.cluster.Cluster.from_nodes

Installing DC/OS
----------------

Some backends support installing DC/OS from a path to a build artifact.
Some backends support installing DC/OS from a URL pointing to a build artifact.

Each backend comes with a default DC/OS configuration which is enough to start an open source DC/OS cluster.
The ``extra_config`` parameter allows you to add to or override these configuration settings.
See :doc:`how to use DC/OS Enterprise <enterprise>` with DC/OS E2E.

.. automethod:: dcos_e2e.cluster.Cluster.install_dcos_from_path

.. automethod:: dcos_e2e.cluster.Cluster.install_dcos_from_url

Destroying a ``Cluster``
------------------------

``Cluster``\s have a ``destroy()`` method.
This can be called manually, or ``Cluster``\s can be used as context managers.
In this case the cluster will be destroyed when exiting the context manager.

.. code:: python

    with Cluster(backend=Docker(), masters=3, agents=2):
        pass

Waiting for DC/OS
-----------------

Depending on the hardware and the backend, DC/OS can take some time to install.
The methods to wait for DC/OS repeatedly poll the cluster until services are up.
Choose the :py:meth:`~dcos_e2e.cluster.Cluster.wait_for_dcos_oss` or :py:meth:`~dcos_e2e.cluster.Cluster.wait_for_dcos_ee` as appropriate.

Running Integration Tests
-------------------------

It is possible to easily run DC/OS integration tests on a cluster.

.. cluster

Reference
---------

.. autoclass:: dcos_e2e.cluster.Cluster
   :members:
