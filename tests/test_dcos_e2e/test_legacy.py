"""
Tests for support of legacy versions of DC/OS.

We do not test the whole matrix of support, such as each version with each
Docker version or base operating system, for cost reasons.
"""

from pathlib import Path

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster


class Test_1_10:
    """
    Tests for running DC/OS 1.10.
    """

    def test_oss(
        self,
        cluster_backend: ClusterBackend,
        oss_1_10_artifact: Path,
    ) -> None:
        """
        An open source DC/OS 1.10 cluster can be started.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                build_artifact=oss_1_10_artifact,
                log_output_live=True,
            )
            cluster.wait_for_dcos_oss()

    def test_enterprise(
        self,
        cluster_backend: ClusterBackend,
        enterprise_1_10_artifact: Path,
    ) -> None:
        """
        Integration tests can be run with `pytest`.
        Errors are raised from `pytest`.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                build_artifact=enterprise_1_10_artifact,
                extra_config=config,
                log_output_live=True,
            )
            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )
