|Build Status|

|codecov|

|Updates|

|Documentation Status|

DC/OS E2E
=========

DC/OS E2E is a tool for spinning up and managing DC/OS clusters in test environments.

.. contents::

Installation
------------

Requires Python 3.5.2+.

.. code:: sh

    pip install --process-dependency-links git+https://github.com/mesosphere/dcos-e2e.git@master

Python Library
--------------

Below is a small example of using DC/OS E2E as a Python library with a Docker backend.
See the `full documentation <http://dcos-e2e.readthedocs.io/en/latest/?badge=latest>`_ for more details on these and other features.

.. code:: python

    from pathlib import Path

    from dcos_e2e.backends import Docker
    from dcos_e2e.cluster import Cluster

    oss_artifact = Path('/tmp/dcos_generate_config.sh')

    with Cluster(cluster_backend=Docker()) as cluster:
        cluster.install_dcos_from_path(
            build_artifact=oss_artifact,
            extra_config={'check_time': True},
        )
        (master, ) = cluster.masters
        result = master.run(
            args=['test', '-f', path],
            user=cluster.default_ssh_user,
        )
        print(result.stdout)
        cluster.wait_for_dcos_oss()
        cluster.run_integration_tests(pytest_command=['pytest', '-x', 'test_tls.py'])

CLI
---

There is also a CLI tool.
This is useful for quickly creating, managing and destroying clusters.

An typical CLI workflow may look like this:

.. code-block:: console

   $ dcos_docker create /tmp/dcos_generate_config.sh --agents 0 --cluster-id default
   default
   $ dcos_docker create /tmp/dcos_generate_config.sh --agents 5
   921214100
   $ dcos_docker wait # Uses "default" by default
   $ dcos_docker run --sync . pytest -k test_tls
   ...
   $ dcos_docker destroy $(dcos_docker list)

Each of these commands and more described in detail in the `full CLI documentation <http://dcos-e2e.readthedocs.io/en/latest/cli.html>`_.

.. |Build Status| image:: https://travis-ci.org/mesosphere/dcos-e2e.svg?branch=master
   :target: https://travis-ci.org/mesosphere/dcos-e2e
.. |codecov| image:: https://codecov.io/gh/mesosphere/dcos-e2e/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/mesosphere/dcos-e2e
.. |Updates| image:: https://pyup.io/repos/github/mesosphere/dcos-e2e/shield.svg
   :target: https://pyup.io/repos/github/mesosphere/dcos-e2e/
.. |Documentation Status| image:: https://readthedocs.org/projects/dcos-e2e/badge/?version=latest
   :target: http://dcos-e2e.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
