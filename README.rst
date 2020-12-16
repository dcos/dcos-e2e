|Actions build status|

|Build Status|

|codecov|

|Library Documentation Status| **: Library**

|CLI Documentation Status| **: miniDC/OS**

|project|
=========

|project| is a tool for spinning up and managing DC/OS clusters in test environments.
It includes a Python library and miniDC/OS CLI tools.

See the full documentation on Read the Docs for the `library`_ and `miniDC/OS`_.

.. contents::
   :local:

Installation
------------

|project| consists of a Python `library`_ and `miniDC/OS`_.

See the full `miniDC/OS`_ documentation for CLI installation options.

To install the library, follow the `library installation instructions`_.

Python Library
--------------

Below is a small example of using |project| as a Python library with a Docker backend.
Other backends include AWS and Vagrant.
See the `library`_ documentation for more details on these and other features.

.. code:: python

    from pathlib import Path

    from dcos_e2e.backends import Docker
    from dcos_e2e.cluster import Cluster

    oss_installer = Path('/tmp/dcos_generate_config.sh')

    cluster_backend = Docker()
    with Cluster(cluster_backend=cluster_backend) as cluster:
        cluster.install_dcos_from_path(
            dcos_installer=oss_installer,
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
        cluster.run_with_test_environment(args=['pytest', '-x', 'test_tls.py'])

miniDC/OS CLI
-------------

|project| also provides multiple command line interface tools.
These allow you to create, manage and destroy DC/OS clusters on various backends, such as Docker, Vagrant and AWS.

A typical CLI workflow with the ``minidcos docker`` CLI may look like this:

.. code-block:: bash

   # Fix issues shown by ``minidcos docker doctor``
   $ minidcos docker doctor
   $ minidcos docker download-installer
   $ minidcos docker create ./dcos_generate_config.sh --agents 0
   default
   $ minidcos docker wait
   $ minidcos docker run --test-env --sync-dir /path/to/dcos/checkout pytest -k test_tls
   ...
   # Get onto a node
   $ minidcos docker run bash
   [master-0]# exit
   $ minidcos docker destroy


Each of these commands and more are described in detail in the full `minidcos docker CLI`_ documentation.
Other CLI tools include ``minidcos aws`` and ``minidcos vagrant``.

See the full `miniDC/OS`_ documentation for information on other CLI tools provided by |project|.

.. |Actions build status| image:: https://github.com/dcos/dcos-e2e/workflows/dcos-e2e-test/badge.svg
.. |Build Status| image:: https://travis-ci.org/dcos/dcos-e2e.svg?branch=master
   :target: https://travis-ci.org/dcos/dcos-e2e
.. |codecov| image:: https://codecov.io/gh/dcos/dcos-e2e/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/dcos/dcos-e2e
.. |Library Documentation Status| image:: https://readthedocs.org/projects/dcos-e2e/badge/?version=latest
   :target: http://dcos-e2e.readthedocs.io/en/latest/?badge=latest
   :alt: Library Documentation Status
.. |CLI Documentation Status| image:: https://readthedocs.org/projects/minidcos/badge/?version=latest
   :target: http://minidcos.readthedocs.io/en/latest/?badge=latest
   :alt: CLI Documentation Status
.. _Homebrew: https://brew.sh
.. _Linuxbrew: https://docs.brew.sh/Homebrew-on-Linux
.. _miniDC/OS: https://minidcos.readthedocs.io/en/latest/
.. _minidcos docker CLI: https://minidcos.readthedocs.io/en/latest/dcos-docker-cli.html
.. _library: https://dcos-e2e.readthedocs.io/en/latest/
.. _backends: https://dcos-e2e.readthedocs.io/en/latest/backends.html
.. |project| replace:: DC/OS E2E
.. _library installation instructions: https://dcos-e2e.readthedocs.io/en/latest/installation.html
