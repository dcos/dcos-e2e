"""
Tests for using the test harness with a DC/OS Enterprise cluster.
"""

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster


class TestEnterpriseIntegrationTests:
    """
    Tests for running integration tests on a node.
    """

    def test_run_pytest(
        self,
        enterprise_cluster_backend: ClusterBackend,
    ) -> None:
        """
        Integration tests can be run with `pytest`.
        Errors are raised from `pytest`.
        """
        with Cluster(
            cluster_backend=enterprise_cluster_backend,
            enterprise_cluster=True,
        ) as cluster:
            # No error is raised with a successful command.
            pytest_command = ['pytest', '-vvv', '-s', '-x', 'test_tls.py']
            cluster.run_integration_tests(pytest_command=pytest_command)
