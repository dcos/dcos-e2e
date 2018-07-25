"""
Tests for installing DC/OS on cluster nodes.
"""

from pathlib import Path
from textwrap import dedent

# See https://github.com/PyCQA/pylint/issues/1536 for details on why the errors
# are disabled.
from py.path import local  # pylint: disable=no-name-in-module, import-error

from dcos_e2e.backends import ClusterBackend, Docker
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


class TestCopyFiles:
    """
    Test copying files to the ``genconf`` directory before installing
    DC/OS on a node.
    """

    def test_install_from_path_with_genconf_files(
        self,
        cluster_backend: ClusterBackend,
        oss_artifact: Path,
        tmpdir: local,
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
            ip_detect_file = tmpdir.join('ip-detect')
            ip_detect_contents = dedent(
                """\
                #!/bin/bash
                echo {ip_address}
                """,
            ).format(ip_address=master.private_ip_address)
            ip_detect_file.write(ip_detect_contents)

            master.install_dcos_from_path(
                build_artifact=oss_artifact,
                dcos_config=cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
                # Test that this overwrites the ``ip-detect`` script given
                # by ``ip_detect_path``.
                files_to_copy_to_genconf_dir=[
                    (Path(str(ip_detect_file)), Path('/genconf/ip-detect')),
                ],
                role=Role.MASTER,
            )
            cluster.wait_for_dcos_oss()
            cat_result = master.run(
                args=['cat', '/opt/mesosphere/bin/detect_ip'],
            )
            assert cat_result.stdout.decode() == ip_detect_contents
