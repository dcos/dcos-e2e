Getting Started
---------------

To create a DC/OS :py:class:`~dcos_e2e.cluster.Cluster`, you need a backend.
Backends are customizable, but for now let's use a standard :doc:`Docker backend <docker-backend>`.
Each backend has different system requirements.
See the :doc:`Docker backend documentation <docker-backend>` for details of what is needed for the Docker backend.


.. code:: python

    from dcos_e2e.backends import Docker
    from dcos_e2e.cluster import Cluster

    cluster = Cluster(cluster_backend=Docker())

It is also possible to use :py:class:`~dcos_e2e.cluster.Cluster` as a context manager.
Doing this means that the cluster is destroyed on exit.

To install DC/OS on a cluster, you need a DC/OS installer.
You can download one from `the DC/OS releases page <https://dcos.io/releases/>`_.
In this example we will use a open source DC/OS installer downloaded to :file:`/tmp/dcos_generate_config.sh`.

.. code:: python

   from pathlib import Path

   oss_installer = Path('/tmp/dcos_generate_config.sh')

   cluster.install_dcos_from_path(
       dcos_installer=oss_installer,
       dcos_config={
            **cluster.base_config,
            **{
                'resolvers': ['8.8.8.8'],
            },
       }
       ip_detect_path=Docker().ip_detect_path,
   )

   cluster.wait_for_dcos_oss()

With a :py:class:`~dcos_e2e.cluster.Cluster` you can then run commands on arbitrary :py:class:`~dcos_e2e.node.Node`\s.

.. code:: python

    for master in cluster.masters:
        result = master.run(args=['echo', '1'])
        print(result.stdout)

There is much more that you can do with :py:class:`~dcos_e2e.cluster.Cluster`\s and :py:class:`~dcos_e2e.node.Node`\s, and there are other ways to create a cluster.

