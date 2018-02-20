"""
Tests for support of legacy versions of DC/OS.

We do not test the whole matrix of support, such as each version with each
Docker version or base operating system, for cost reasons.
"""

class Test_1_10:
    """
    Tests for running DC/OS 1.10.
    """

    def test_oss(
        self,
        cluster_backend: ClusterBackend,
        oss_artifact: Path,
    ) -> None:
        """
        Integration tests can be run with `pytest`.
        Errors are raised from `pytest`.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(oss_artifact, log_output_live=True)
            cluster.wait_for_dcos_oss()

    def test_enterprise(
        self,
        cluster_backend: ClusterBackend,
        oss_artifact: Path,
    ) -> None:
        """
        Integration tests can be run with `pytest`.
        Errors are raised from `pytest`.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(oss_artifact, log_output_live=True)
            cluster.wait_for_dcos_oss()

class Test_1_10:
    """
    Tests for running DC/OS 1.10.
    """

    def test_oss(
        self,
        cluster_backend: ClusterBackend,
        oss_artifact: Path,
    ) -> None:
        """
        Integration tests can be run with `pytest`.
        Errors are raised from `pytest`.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(oss_artifact, log_output_live=True)
            cluster.wait_for_dcos_oss()

    def test_enterprise(
        self,
        cluster_backend: ClusterBackend,
        oss_artifact: Path,
    ) -> None:
        """
        Integration tests can be run with `pytest`.
        Errors are raised from `pytest`.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(oss_artifact, log_output_live=True)
            cluster.wait_for_dcos_oss()
