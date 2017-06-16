"""
Tests for using the test harness with a DC/OS Enterprise cluster.
"""

import uuid
from pathlib import Path

from passlib.hash import sha512_crypt

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster


class TestEnterpriseIntegrationTests:
    """
    Tests for running integration tests on a node.
    """

    def test_run_pytest(
        self,
        cluster_backend: ClusterBackend,
        enterprise_cluster: Path,
    ) -> None:
        """
        Integration tests can be run with `pytest`.
        Errors are raised from `pytest`.
        """
        superuser_password = str(uuid.uuid4())
        extra_config = {
            'superuser_username': str(uuid.uuid4()),
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
        }

        with Cluster(
            cluster_backend=cluster_backend,
            enterprise_cluster=True,
            extra_config=extra_config,
            superuser_password=superuser_password,
            generate_config_path=enterprise_cluster,
        ) as cluster:
            # No error is raised with a successful command.
            pytest_command = ['pytest', '-vvv', '-s', '-x', 'test_tls.py']
            cluster.run_integration_tests(pytest_command=pytest_command)
