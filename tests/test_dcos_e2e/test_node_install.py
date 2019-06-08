"""
Tests for installing DC/OS on cluster nodes.
"""

from pathlib import Path
from textwrap import dedent

from dcos_e2e.backends import Docker
from dcos_e2e.base_classes import ClusterBackend
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Output, Role


class TestAdvancedInstallationMethod:
    """
    Test installing DC/OS on a node.
    """

    def test_install_dcos_from_url(
        self,
        oss_installer_url: str,
        cluster_backend: ClusterBackend,
    ) -> None:
        """
        It is possible to install DC/OS on a node from a URL.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            for nodes, role in (
                (cluster.masters, Role.MASTER),
                (cluster.agents, Role.AGENT),
                (cluster.public_agents, Role.PUBLIC_AGENT),
            ):
                for node in nodes:
                    node.install_dcos_from_url(
                        dcos_installer=oss_installer_url,
                        dcos_config=cluster.base_config,
                        ip_detect_path=cluster_backend.ip_detect_path,
                        role=role,
                        output=Output.LOG_AND_CAPTURE,
                    )
            cluster.wait_for_dcos_oss()

    def test_install_dcos_from_path(self, oss_installer: Path) -> None:
        """
        It is possible to install DC/OS on a node from a path.
        """
        cluster_backend = Docker()
        with Cluster(cluster_backend=cluster_backend) as cluster:
            for nodes, role in (
                (cluster.masters, Role.MASTER),
                (cluster.agents, Role.AGENT),
                (cluster.public_agents, Role.PUBLIC_AGENT),
            ):
                for node in nodes:
                    node.install_dcos_from_path(
                        dcos_installer=oss_installer,
                        dcos_config=cluster.base_config,
                        ip_detect_path=cluster_backend.ip_detect_path,
                        role=role,
                        output=Output.LOG_AND_CAPTURE,
                    )
            cluster.wait_for_dcos_oss()


class TestCopyFiles:
    """
    Test copying files to the ``genconf`` directory before installing
    DC/OS on a node.
    """

    def test_install_from_path_with_genconf_files(
        self,
        cluster_backend: ClusterBackend,
        oss_installer: Path,
        tmp_path: Path,
    ) -> None:
        """
        It is possible to copy files to the ``genconf`` directory.
        """
        with Cluster(
            cluster_backend=cluster_backend,
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:

            (master, ) = cluster.masters
            ip_detect_file = tmp_path / 'ip-detect'
            ip_detect_contents = dedent(
                """\
                #!/bin/bash
                echo {ip_address}
                """,
            ).format(ip_address=master.private_ip_address)
            ip_detect_file.write_text(ip_detect_contents)

            master.install_dcos_from_path(
                dcos_installer=oss_installer,
                dcos_config=cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
                # Test that this overwrites the ``ip-detect`` script given
                # by ``ip_detect_path``.
                files_to_copy_to_genconf_dir=[
                    (ip_detect_file, Path('/genconf/ip-detect')),
                ],
                role=Role.MASTER,
                output=Output.LOG_AND_CAPTURE,
            )
            cluster.wait_for_dcos_oss()
            cat_result = master.run(
                args=['cat', '/opt/mesosphere/bin/detect_ip'],
            )
            assert cat_result.stdout.decode() == ip_detect_contents
