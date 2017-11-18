"""
Tests for the existing cluster backend.
"""

from pathlib import Path

import pytest

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster


class TestClusterFromNodes:
    """
    Tests for creating a `Cluster` with the `Cluster.from_nodes` method.
    """

    def test_cluster_from_nodes(self) -> None:
        """
        It is possible to create a cluster from existing nodes, but not destroy
        it.
        """
        backend = Docker()
        cluster = Cluster(
            cluster_backend=backend,
            masters=1,
            agents=1,
            public_agents=1,
        )

        (master, ) = cluster.masters
        (agent, ) = cluster.agents
        (public_agent, ) = cluster.public_agents

        with Cluster.from_nodes(
            masters=cluster.masters,
            agents=cluster.agents,
            public_agents=cluster.public_agents,
            default_ssh_user=backend.default_ssh_user,
        ) as duplicate_cluster:
            (duplicate_master, ) = duplicate_cluster.masters
            (duplicate_agent, ) = duplicate_cluster.agents
            (duplicate_public_agent, ) = duplicate_cluster.public_agents

            duplicate_master.run(
                args=['touch', 'example_master_file'],
                user=duplicate_cluster.default_ssh_user,
            )
            duplicate_agent.run(
                args=['touch', 'example_agent_file'],
                user=duplicate_cluster.default_ssh_user,
            )
            duplicate_public_agent.run(
                args=['touch', 'example_public_agent_file'],
                user=duplicate_cluster.default_ssh_user,
            )

            master.run(
                args=['test', '-f', 'example_master_file'],
                user=duplicate_cluster.default_ssh_user,
            )
            agent.run(
                args=['test', '-f', 'example_agent_file'],
                user=duplicate_cluster.default_ssh_user,
            )
            public_agent.run(
                args=['test', '-f', 'example_public_agent_file'],
                user=duplicate_cluster.default_ssh_user,
            )

        with pytest.raises(NotImplementedError):
            duplicate_cluster.destroy()

        cluster.destroy()

    def test_install_dcos(
        self,
        oss_artifact: Path,
        oss_artifact_url: str,
    ) -> None:
        """
        If a user attempts to install DC/OS on is called on a `Cluster` created
        from existing nodes, a `NotImplementedError` is raised.
        """
        backend = Docker()
        with Cluster(
            cluster_backend=backend,
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            cluster = Cluster.from_nodes(
                masters=cluster.masters,
                agents=cluster.agents,
                public_agents=cluster.public_agents,
                default_ssh_user=backend.default_ssh_user,
            )

            with pytest.raises(NotImplementedError):
                cluster.install_dcos_from_url(build_artifact=oss_artifact_url)

            with pytest.raises(NotImplementedError):
                cluster.install_dcos_from_path(build_artifact=oss_artifact)
