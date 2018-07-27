|Build Status|

|codecov|

|Documentation Status|

DC/OS E2E
=========

DC/OS E2E is a tool for spinning up and managing DC/OS clusters in test environments.

See the full documentation on `Read the Docs <http://dcos-e2e.readthedocs.io/>`_.

.. contents::
   :local:

Installation
------------

DC/OS E2E consists of a `library`_ and various `CLI`_ tools.

The tools CLI can be installed with Homebrew on macOS, and the library and CLI can be installed together with ``pip`` on any Linux and macOS.

Windows is not currently supported, but we provide instructions on using DC/OS E2E on Windows with Vagrant on particular `backends`_\ ' documentation.


CLI on macOS With Homebrew or Linux with Linuxbrew
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install the CLI on macOS, install `Homebrew`_.
To install the CLI on Linux, install `Linuxbrew`_.
Or, if you prefer, see "Library and CLI with Python" below for an alternative.

Then install the latest stable version:

.. code:: sh

    brew install https://raw.githubusercontent.com/dcos/dcos-e2e/master/dcose2e.rb

To upgrade from an older version, run the following command:

.. code:: sh

    brew upgrade https://raw.githubusercontent.com/dcos/dcos-e2e/master/dcose2e.rb

Run ``dcos-docker doctor`` to make sure that your system is ready to go for the ``dcos-docker`` CLI:

.. code-block:: console

   $ dcos-docker doctor

Library and CLI with Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the CLI has been installed with Homebrew or Linuxbrew, you do not need to install the library to use the CLI.

Requires Python 3.5.2+.
To avoid interfering with your system's Python, we recommend using a `virtualenv <https://virtualenv.pypa.io/en/stable/>`_.

Check the Python version:

.. code:: sh

   python3 --version

On Fedora, install Python development requirements:

.. code:: sh

   sudo dnf install -y git python3-devel

On Ubuntu, install Python development requirements:

.. code:: sh

   apt install -y gcc python3-dev

Optionally replace ``master`` with a particular version of DC/OS E2E.
See `available versions <https://github.com/dcos/dcos-e2e/tags>`_.

If you are not in a virtualenv, you may have to use ``sudo`` before the following command, or ``--user`` after ``install``.

.. code:: sh

    pip3 install --upgrade git+https://github.com/dcos/dcos-e2e.git@master

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

DC/OS E2E also provides multiple command line interface tools.
These allow you to create, manage and destroy DC/OS clusters on various backends.

A typical CLI workflow with the ``dcos-docker`` CLI may look like this:

.. code-block:: console

   # Fix issues shown by dcos-docker doctor
   $ dcos-docker doctor
   $ dcos-docker download-artifact
   $ dcos-docker create /tmp/dcos_generate_config.sh --agents 0
   default
   $ dcos-docker wait
   $ dcos-docker run --sync-dir /path/to/dcos/checkout pytest -k test_tls
   ...
   # Get onto a node
   $ dcos-docker run bash
   $ dcos-docker destroy


Each of these commands and more are described in detail in the full `dcos-docker CLI`_ documentation.

See the full `CLI`_ documentation for information on other CLI tools provided by DC/OS E2E.

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
