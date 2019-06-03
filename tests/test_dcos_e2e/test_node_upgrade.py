class TestNodeUpgrade:

    def test_node_upgrade(
        self,
        oss_1_13_installer: Path,
        oss_master_installer: Path,
    ) -> None:
        # TODO(tweidner): Remove this since 18.09 will be the default.
        # We use a specific version of Docker on the nodes because else we may
        # hit https://github.com/opencontainers/runc/issues/1175.
        cluster_backend = Docker(docker_version=DockerVersion.v17_12_1_ce)
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                dcos_installer=oss_1_13_installer,
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
                    node.upgrade_from_dcos_path(
                        dcos_installer=oss_installer,
                        dcos_config=cluster.base_config,
                        ip_detect_path=cluster_backend.ip_detect_path,
                        role=role,
                    )

            cluster.wait_for_dcos_oss()
            for node in nodes:
                node.dcos_version
                # node.download_file(version_file...
                # as
