"""
Tests for the existing cluster backend.
"""

from pathlib import Path
from typing import Iterator

import pytest

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster


class TestExistingCluster:
    """
    Tests for creating a `Cluster` with the `Cluster.from_nodes` method.
    """

    def test_existing_cluster(self, oss_artifact: Path) -> None:
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


class TestUnsupportedInstallationMethods:
    """
    Tests for unsupported installation methods.
    """

    @pytest.fixture()
    def cluster(self) -> Iterator[Cluster]:
        """
        Return an `Cluster` with the nodes from an existing cluster.
        """
        backend = Docker()
        with Cluster(
            cluster_backend=backend,
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            yield Cluster.from_nodes(
                masters=cluster.masters,
                agents=cluster.agents,
                public_agents=cluster.public_agents,
                default_ssh_user=backend.default_ssh_user,
            )

    def test_install_dcos_from_url(
        self,
        cluster: Cluster,
        oss_artifact_url: str,
    ) -> None:
        """
        If `install_dcos_from_url` is called on a `Cluster` created from
        existing nodes, a `NotImplementedError` is raised.
        """
        with pytest.raises(NotImplementedError) as excinfo:
            cluster.install_dcos_from_url(build_artifact=oss_artifact_url)

        expected_error = (
            'The ExistingCluster backend does not support installing '
            'DC/OS because it is assumed that an instance of DC/OS is '
            'already installed and running on the cluster.'
        )

        assert str(excinfo.value) == expected_error

    def test_install_dcos_from_path(
        self,
        cluster: Cluster,
        oss_artifact: Path,
    ) -> None:
        """
        If `install_dcos_from_path` is called on a `Cluster` created from
        existing nodes, a `NotImplementedError` is raised.
        """
        with pytest.raises(NotImplementedError) as excinfo:
            cluster.install_dcos_from_path(build_artifact=oss_artifact)

        expected_error = (
            'The ExistingCluster backend does not support installing '
            'DC/OS because it is assumed that an instance of DC/OS is '
            'already installed and running on the cluster.'
        )

        assert str(excinfo.value) == expected_error
