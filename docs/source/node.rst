Cluster ``Node``\s
==================

:py:class:`~dcos_e2e.cluster.Cluster`\s are made of :py:class:`~dcos_e2e.node.Node`\s.
The :py:class:`~dcos_e2e.node.Node` interface is backend agnostic.

:py:class:`~dcos_e2e.node.Node`\s are generally used to run commands.

:py:class:`~dcos_e2e.node.Node`\s are either manually constructed in order to create a :py:meth:`~dcos_e2e.cluster.Cluster.from_nodes`, or they are retrieved from an existing :py:class:`~dcos_e2e.cluster.Cluster`.

.. autoclass:: dcos_e2e.node.Node

Running a Command on a Node
---------------------------

There are two methods used to run commands on :py:class:`~dcos_e2e.node.Node`\s.
``run`` and ``popen`` are roughly equivalent to their :py:mod:`subprocess` namesakes.

.. automethod:: dcos_e2e.node.Node.run

.. automethod:: dcos_e2e.node.Node.popen

Sending a File to a Node
------------------------

.. automethod:: dcos_e2e.node.Node.send_file
