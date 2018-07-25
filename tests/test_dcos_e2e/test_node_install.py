"""
Tests for installing DC/OS on cluster nodes.
"""

from pathlib import Path

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.docker_versions import DockerVersion
from dcos_e2e.node import Role


class TestAdvancedInstallationMethod:
    """
    Test installing DC/OS on a node.
    """

    def test_install_dcos_from_url(self, oss_artifact_url: str) -> None:
        """
        It is possible to install DC/OS on a node from a URL.
        """
        # We use a specific version of Docker on the nodes because else we may
        # hit https://github.com/opencontainers/runc/issues/1175.
        cluster_backend = Docker(docker_version=DockerVersion.v17_12_1_ce)
        with Cluster(cluster_backend=cluster_backend) as cluster:
            for nodes, role in (
                (cluster.masters, Role.MASTER),
                (cluster.agents, Role.AGENT),
                (cluster.public_agents, Role.PUBLIC_AGENT),
            ):
                for node in nodes:
                    node.install_dcos_from_url(
                        build_artifact=oss_artifact_url,
                        dcos_config=cluster.base_config,
                        ip_detect_path=cluster_backend.ip_detect_path,
                        role=role,
                    )
            cluster.wait_for_dcos_oss()

    def test_install_dcos_from_path(self, oss_artifact: Path) -> None:
        """
        It is possible to install DC/OS on a node from a path.
        """
        # We use a specific version of Docker on the nodes because else we may
        # hit https://github.com/opencontainers/runc/issues/1175.
        cluster_backend = Docker(docker_version=DockerVersion.v17_12_1_ce)
        with Cluster(cluster_backend=cluster_backend) as cluster:
            for nodes, role in (
                (cluster.masters, Role.MASTER),
                (cluster.agents, Role.AGENT),
                (cluster.public_agents, Role.PUBLIC_AGENT),
            ):
                for node in nodes:
                    node.install_dcos_from_path(
                        build_artifact=oss_artifact,
                        dcos_config=cluster.base_config,
                        ip_detect_path=cluster_backend.ip_detect_path,
                        role=role,
                    )
            cluster.wait_for_dcos_oss()
