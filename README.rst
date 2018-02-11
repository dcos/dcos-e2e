|Build Status|

|codecov|

|Updates|

|Documentation Status|

DC/OS E2E
=========

Spin up DC/OS clusters with various configurations and run tests using those clusters.

Interactions can be "end to end", meaning that you can test start up and shut down of clusters.

Requires Python 3.5.2+.

Installation
------------

.. code:: sh

    pip install --process-dependency-links git+https://github.com/mesosphere/dcos-e2e.git@master

Usage
-----

Below is an example test with a Docker backend.
See the full documentation for mode details.

.. code:: python

    from pathlib import Path

    from dcos_e2e.backends import Docker
    from dcos_e2e.cluster import Cluster

    def test_oss_example():

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

See the `full documentation <http://dcos-e2e.readthedocs.io/en/latest/?badge=latest>`_ for more details.

.. |Build Status| image:: https://travis-ci.org/mesosphere/dcos-e2e.svg?branch=master
   :target: https://travis-ci.org/mesosphere/dcos-e2e
.. |codecov| image:: https://codecov.io/gh/mesosphere/dcos-e2e/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/mesosphere/dcos-e2e
.. |Updates| image:: https://pyup.io/repos/github/mesosphere/dcos-e2e/shield.svg
   :target: https://pyup.io/repos/github/mesosphere/dcos-e2e/
.. |Documentation Status| image:: https://readthedocs.org/projects/dcos-e2e/badge/?version=latest
   :target: http://dcos-e2e.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
