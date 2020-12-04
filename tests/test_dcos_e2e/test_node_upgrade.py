"""
Tests for upgrading DC/OS on nodes.
"""

from pathlib import Path

from dcos_e2e.base_classes import ClusterBackend
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import DCOSVariant, Output, Role


class TestNodeUpgradeFromPath:
    """
    Tests for ``Node.upgrade_dcos_from_path``.
    """

    def test_node_upgrade(
        self,
        oss_2_0_installer: Path,
        oss_2_1_installer: Path,
        cluster_backend: ClusterBackend,
    ) -> None:
        """
        DC/OS OSS can be upgraded from 2.0 to 2.1.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                dcos_installer=oss_2_0_installer,
                dcos_config=cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
                output=Output.LOG_AND_CAPTURE,
            )
            cluster.wait_for_dcos_oss()

            for nodes, role in (
                (cluster.masters, Role.MASTER),
                (cluster.agents, Role.AGENT),
                (cluster.public_agents, Role.PUBLIC_AGENT),
            ):
                for node in nodes:
                    build = node.dcos_build_info()
                    assert build.version.startswith('2.0')
                    assert build.variant == DCOSVariant.OSS
                    node.upgrade_dcos_from_path(
                        dcos_installer=oss_2_1_installer,
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
                assert build.version.startswith('2.1')
                assert build.variant == DCOSVariant.OSS
