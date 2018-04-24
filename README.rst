|Build Status|

|codecov|

|Updates|

|Documentation Status|

DC/OS E2E
=========

DC/OS E2E is a tool for spinning up and managing DC/OS clusters in test environments.

See the full documentation on `Read the Docs <http://dcos-e2e.readthedocs.io/>`_.

.. contents::
   :local:

Installation
------------

DC/OS E2E consists of a `library`_ and a `CLI`_.

The CLI works only with the `Docker backend`_, while the library supports multiple `backends`_.
The CLI can be installed with Homebrew on macOS, and the library and CLI can be installed together with ``pip`` on any Linux and macOS.

Windows is not currently supported, but we provide instructions on using DC/OS E2E on Windows with Vagrant on particular `backends`_\ ' documentation.

.. _library: http://dcos-e2e.readthedocs.io/en/latest/library.html
.. _CLI: http://dcos-e2e.readthedocs.io/en/latest/cli.html
.. _Docker backend: http://dcos-e2e.readthedocs.io/en/latest/docker-backend.html
.. _backends: http://dcos-e2e.readthedocs.io/en/latest/backends.html

CLI macOS With Homebrew
~~~~~~~~~~~~~~~~~~~~~~~

To install the CLI on macOS, install `Homebrew`_.

Then install the latest stable version:

.. code:: sh

    brew install https://raw.githubusercontent.com/mesosphere/dcos-e2e/master/dcosdocker.rb

To upgrade from an older version, run the following command:

.. code:: sh

    brew upgrade https://raw.githubusercontent.com/mesosphere/dcos-e2e/master/dcosdocker.rb

Run ``dcos-docker doctor`` to make sure that your system is ready to go for the Docker backend:

.. code-block:: console

   $ dcos-docker doctor

Library and CLI with Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the CLI has been installed with Homebrew, you do not need to install the library to use the CLI.

Requires Python 3.5.2+.

Check the Python version:

.. code:: sh

   python3 --version

Optionally replace ``master`` with a particular version of DC/OS E2E.
See `available versions <https://github.com/mesosphere/dcos-e2e/tags>`_.

.. code:: sh

    pip3 install git+https://github.com/mesosphere/dcos-e2e.git@master

Run ``dcos-docker doctor`` to make sure that your system is ready to go for the Docker backend:

.. code-block:: console

   $ dcos-docker doctor

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
        result = master.run(args=['echo', '1'])
        print(result.stdout)
        cluster.wait_for_dcos_oss()
        cluster.run_integration_tests(pytest_command=['pytest', '-x', 'test_tls.py'])

CLI
---

There is also a CLI tool.
This is useful for quickly creating, managing and destroying clusters.

A typical CLI workflow may look like this:

.. code-block:: console

   # Fix issues shown by dcos-docker doctor
   $ dcos-docker doctor
   $ dcos-docker create /tmp/dcos_generate_config.sh --agents 0 --cluster-id default
   default
   # Without specifying a cluster ID for ``wait`` and ``run``, ``default``
   # is automatically used.
   $ dcos-docker wait
   $ dcos-docker run --sync-dir /path/to/dcos/checkout pytest -k test_tls
   ...
   $ dcos-docker destroy

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
.. _Homebrew: https://brew.sh
