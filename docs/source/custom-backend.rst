Custom Backends
===============

DC/OS E2E supports pluggable backends.
You may wish to create a new backend to support a new cloud provider for example.

To create a cluster :doc:`Cluster <cluster>` backend, you need to create two classes.
You need to create a :py:class:`~dcos_e2e.backends._base_classes.ClusterManager` and a :py:class:`~dcos_e2e.backends._base_classes.ClusterBackend`.


Please consider contributing your backend to this repository if it is stable and could be of value to a wider audience.

.. autoclass:: dcos_e2e.backends._base_classes.ClusterBackend
   :members:

.. autoclass:: dcos_e2e.backends._base_classes.ClusterManager
   :members:
