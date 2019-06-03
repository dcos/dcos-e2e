Cluster ``Node``\s
==================

:py:class:`~dcos_e2e.cluster.Cluster`\s are made of :py:class:`~dcos_e2e.node.Node`\s.
The :py:class:`~dcos_e2e.node.Node` interface is backend agnostic.

:py:class:`~dcos_e2e.node.Node`\s are generally used to run commands.

:py:class:`~dcos_e2e.node.Node`\s are either manually constructed in order to create a :py:meth:`~dcos_e2e.cluster.Cluster.from_nodes`, or they are retrieved from an existing :py:class:`~dcos_e2e.cluster.Cluster`.

.. automodule:: dcos_e2e.node
   :members:
   :undoc-members:
