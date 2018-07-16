from pathlib import Path

from py.path import local  # pylint: disable=no-name-in-module, import-error

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Role


class TestCustomIPDetect:
    """
    Users can specify a custom ``ip-detect``.
    """

    def test_install_node_from_path(
        self,
        cluster_backend: ClusterBackend,
        oss_artifact: Path,
        tmpdir: local,
    ) -> None:
        """
        Install DC/OS with a custom ``ip-detect`` script node by node.
        """
        with Cluster(
            cluster_backend=cluster_backend,
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:

            (master, ) = cluster.masters
            ip_detect_file = tmpdir.join('ip-detect')
            ip_detect_contents = (
                '#!/bin/bash\n'
                'echo {ip_address}'
            ).format(ip_address=master.private_ip_address)
            ip_detect_file.write(ip_detect_contents)

            master.install_dcos_from_path(
                build_artifact=oss_artifact,
                dcos_config=cluster.base_config,
                role=Role.MASTER,
                files_to_copy_to_genconf_dir=[
                    (Path(str(ip_detect_file)), Path('genconf/ip-detect')),
                ],
            )
            cluster.wait_for_dcos_oss()
            cat_result = master.run(
                args=['cat', '/opt/mesosphere/bin/ip_detect'],
            )
            assert cat_result.stdout.decode() == ip_detect_contents

    def test_install_cluster_from_path(
        self,
        cluster_backend: ClusterBackend,
        oss_artifact: Path,
        tmpdir: local,
    ) -> None:
        """
        Install a DC/OS cluster with a custom ``ip-detect`` script.
        """
        with Cluster(
            cluster_backend=cluster_backend,
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:

            (master, ) = cluster.masters
            ip_detect_file = tmpdir.join('ip-detect')
            ip_detect_contents = (
                '#!/bin/bash\n'
                'echo {ip_address}'
            ).format(ip_address=master.private_ip_address)
            ip_detect_file.write(ip_detect_contents)

            cluster.install_dcos_from_path(
                build_artifact=oss_artifact,
                dcos_config=cluster.base_config,
                files_to_copy_to_genconf_dir=[
                    (Path(str(ip_detect_file)), Path('genconf/ip-detect')),
                ],
            )
            master.wait_for_dcos()
            cat_result = master.run(
                args=['cat', '/opt/mesosphere/bin/ip_detect'],
            )
            assert cat_result.stdout.decode() == ip_detect_contents
