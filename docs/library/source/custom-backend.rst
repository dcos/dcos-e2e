Custom Backends
===============

|project| supports pluggable backends.
You may wish to create a new backend to support a new cloud provider for example.

How to Create a Custom Backend
------------------------------

To create a cluster :doc:`Cluster <cluster>` backend, you need to create two classes.
You need to create a :py:class:`~dcos_e2e.base_classes.ClusterManager` and a :py:class:`~dcos_e2e.base_classes.ClusterBackend`.

A :py:class:`~dcos_e2e.base_classes.ClusterBackend` may take custom parameters and is useful for storing backend-specific options.
A :py:class:`~dcos_e2e.base_classes.ClusterManager` implements the nuts and bolts of cluster management for a particular backend.
This implements things like creating nodes and installing DC/OS on those nodes.

Please consider contributing your backend to this repository if it is stable and could be of value to a wider audience.

References
----------

.. autoclass:: dcos_e2e.base_classes.ClusterBackend
   :members:

.. autoclass:: dcos_e2e.base_classes.ClusterManager
   :members:
