|Build Status|

|codecov|

|Documentation Status|

|project|
=========

|project| is a tool for spinning up and managing DC/OS clusters in test environments.
It includes a Python library and various CLI tools.

See the full documentation on `Read the Docs <http://dcos-e2e.readthedocs.io/>`_.

.. contents::
   :local:

Installation
------------

|project| consists of a Python `library`_ and various `CLI`_ tools.

See the full `CLI`_ documentation for CLI installation options.

To install the library, follow the `library installation instructions`_.

Python Library
--------------

Below is a small example of using |project| as a Python library with a Docker backend.
See the `full documentation <http://dcos-e2e.readthedocs.io/en/latest/?badge=latest>`_ for more details on these and other features.

.. code:: python

    from pathlib import Path

    from dcos_e2e.backends import Docker
    from dcos_e2e.cluster import Cluster

    oss_artifact = Path('/tmp/dcos_generate_config.sh')

    cluster_backend = Docker()
    with Cluster(cluster_backend=cluster_backend) as cluster:
        cluster.install_dcos_from_path(
            build_artifact=oss_artifact,
            dcos_config={
                **cluster.base_config,
                **{
                    'check_time': True,
                },
            },
            ip_detect_path=cluster_backend.ip_detect_path,
        )
        (master, ) = cluster.masters
        result = master.run(args=['echo', '1'])
        print(result.stdout)
        cluster.wait_for_dcos_oss()
        cluster.run_integration_tests(pytest_command=['pytest', '-x', 'test_tls.py'])

CLI
---

|project| also provides multiple command line interface tools.
These allow you to create, manage and destroy DC/OS clusters on various backends.

A typical CLI workflow with the ``dcos-docker`` CLI may look like this:

.. code-block:: console

   # Fix issues shown by dcos-docker doctor
   $ dcos-docker doctor
   $ dcos-docker download-artifact
   $ dcos-docker create ./dcos_generate_config.sh --agents 0
   default
   $ dcos-docker wait
   $ dcos-docker run --sync-dir /path/to/dcos/checkout pytest -k test_tls
   ...
   # Get onto a node
   $ dcos-docker run bash
   $ dcos-docker destroy


Each of these commands and more are described in detail in the full `dcos-docker CLI`_ documentation.

See the full `CLI`_ documentation for information on other CLI tools provided by |project|.

.. |Build Status| image:: https://travis-ci.org/dcos/dcos-e2e.svg?branch=master
   :target: https://travis-ci.org/dcos/dcos-e2e
.. |codecov| image:: https://codecov.io/gh/dcos/dcos-e2e/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/dcos/dcos-e2e
.. |Documentation Status| image:: https://readthedocs.org/projects/dcos-e2e/badge/?version=latest
   :target: http://dcos-e2e.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
.. _Homebrew: https://brew.sh
.. _Linuxbrew: https://linuxbrew.sh
.. _CLI: http://dcos-e2e.readthedocs.io/en/latest/cli.html
.. _dcos-docker CLI: http://dcos-e2e.readthedocs.io/en/latest/dcos-docker-cli.html
.. _library: http://dcos-e2e.readthedocs.io/en/latest/library.html
.. _backends: http://dcos-e2e.readthedocs.io/en/latest/backends.html
.. |project| replace:: DC/OS E2E
.. _library installation instructions: https://dcos-e2e.readthedocs.io/en/latest/installation.html#library-and-cli-with-python
