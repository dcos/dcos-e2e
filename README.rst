|Build Status|

|codecov|

|Updates|

|Documentation Status|

DC/OS E2E
=========

DC/OS E2E is a tool for spinning up and managing DC/OS clusters in test environments.

.. contents::
   :title:

Installation
------------

Requires Python 3.5.2+.

.. code:: sh

    pip install --process-dependency-links git+https://github.com/mesosphere/dcos-e2e.git@master

Usage
-----

Below is a small example with a Docker backend.
See the `full documentation <http://dcos-e2e.readthedocs.io/en/latest/?badge=latest>`_ for more details.

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

.. |Build Status| image:: https://travis-ci.org/mesosphere/dcos-e2e.svg?branch=master
   :target: https://travis-ci.org/mesosphere/dcos-e2e
.. |codecov| image:: https://codecov.io/gh/mesosphere/dcos-e2e/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/mesosphere/dcos-e2e
.. |Updates| image:: https://pyup.io/repos/github/mesosphere/dcos-e2e/shield.svg
   :target: https://pyup.io/repos/github/mesosphere/dcos-e2e/
.. |Documentation Status| image:: https://readthedocs.org/projects/dcos-e2e/badge/?version=latest
   :target: http://dcos-e2e.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
