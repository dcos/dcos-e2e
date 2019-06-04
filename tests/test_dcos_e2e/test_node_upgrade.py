"""
Tests for upgrading DC/OS on nodes.
"""

from pathlib import Path

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import DCOSVariant, Output, Role


class TestNodeUpgradeFromPath:
    """
    Tests for ``Node.upgrade_dcos_from_path``.
    """

    def test_node_upgrade(
        self,
        oss_1_12_installer: Path,
        oss_1_13_installer: Path,
    ) -> None:
        """
        DC/OS OSS can be upgraded from 1.12 to 1.13.
        """
        cluster_backend = Docker()
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                dcos_installer=oss_1_12_installer,
                dcos_config=cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
            )
            cluster.wait_for_dcos_oss()

            for nodes, role in (
                (cluster.masters, Role.MASTER),
                (cluster.agents, Role.AGENT),
                (cluster.public_agents, Role.PUBLIC_AGENT),
            ):
                for node in nodes:
                    build = node.dcos_build_info()
                    assert build.version.startswith('1.12')
                    assert build.variant == DCOSVariant.OSS
                    node.upgrade_dcos_from_path(
                        dcos_installer=oss_1_13_installer,
                        dcos_config=cluster.base_config,
                        ip_detect_path=cluster_backend.ip_detect_path,
                        role=role,
                        output=Output.LOG_AND_CAPTURE,
                    )

            cluster.wait_for_dcos_oss()
            for node in {
                *cluster.masters,
                *cluster.agents,
                *cluster.public_agents,
            }:
                build = node.dcos_build_info()
                assert build.version.startswith('1.13')
                assert build.variant == DCOSVariant.OSS
