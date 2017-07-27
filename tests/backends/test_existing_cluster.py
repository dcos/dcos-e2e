"""
Tests for the existing cluster backend.
"""

from pathlib import Path

import pytest

from dcos_e2e.backends import ClusterBackend, DCOS_Docker, ExistingCluster
from dcos_e2e.cluster import Cluster


class TestExistingCluster:
    """
    Tests for creating a `Cluster` with the `ExistingCluster` backend.
    """

    def test_existing_cluster(self, oss_artifact: Path) -> None:
        """
        It is possible to create a cluster from existing nodes, but not destroy
        it.
        """
        with Cluster(
            cluster_backend=DCOS_Docker(),
            generate_config_path=oss_artifact,
            masters=1,
            agents=1,
            public_agents=1,
            destroy_on_success=False,
        ) as cluster:
            (master, ) = cluster.masters
            (agent, ) = cluster.agents
            (public_agent, ) = cluster.public_agents

            existing_cluster = ExistingCluster(
                masters=cluster.masters,
                agents=cluster.agents,
                public_agents=cluster.public_agents,
            )

            with Cluster(
                cluster_backend=existing_cluster,
                masters=len(cluster.masters),
                agents=len(cluster.agents),
                public_agents=len(cluster.public_agents),
                destroy_on_success=False,
                destroy_on_error=False,
            ) as duplicate_cluster:
                (duplicate_master, ) = duplicate_cluster.masters
                (duplicate_agent, ) = duplicate_cluster.agents
                (duplicate_public_agent, ) = duplicate_cluster.public_agents

                duplicate_master.run(
                    args=['touch', 'example_master_file'],
                    user='root',
                )
                duplicate_agent.run(
                    args=['touch', 'example_agent_file'],
                    user='root',
                )
                duplicate_public_agent.run(
                    args=['touch', 'example_public_agent_file'],
                    user='root',
                )

                master.run(
                    args=['test', '-f', 'example_master_file'], user='root'
                )
                agent.run(
                    args=['test', '-f', 'example_agent_file'], user='root'
                )
                public_agent.run(
                    args=['test', '-f', 'example_public_agent_file'],
                    user='root',
                )

            with pytest.raises(NotImplementedError):
                duplicate_cluster.destroy()

            cluster.destroy()


class TestBadParameters:
    """
    Tests for unexpected parameter values.
    """

    @pytest.fixture(scope='module')
    def dcos_cluster(self, oss_artifact: Path) -> Cluster:
        """
        Return a `Cluster`.

        This is module scoped as we do not intend to modify the cluster.
        """
        with Cluster(
            cluster_backend=DCOS_Docker(),
            generate_config_path=oss_artifact,
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            yield cluster

    @pytest.fixture()
    def existing_cluster_backend(
        self, dcos_cluster: Cluster
    ) -> ClusterBackend:
        """
        Return an `ExistingCluster` with the nodes from `dcos_cluster`.
        """
        return ExistingCluster(
            masters=dcos_cluster.masters,
            agents=dcos_cluster.agents,
            public_agents=dcos_cluster.public_agents,
        )

    def test_destroy_on_error(
        self,
        dcos_cluster: Cluster,
        existing_cluster_backend: ClusterBackend,
    ) -> None:
        """
        If `destroy_on_error` is set to `True` an error is raised.
        """
        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=existing_cluster_backend,
                masters=len(dcos_cluster.masters),
                agents=len(dcos_cluster.agents),
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=True,
                destroy_on_success=False,
            ):
                pass  # pragma: no cover

        expected_error = (
            'The given cluster backend does not support being destroyed.'
            ' Therefore, `destroy_on_error` must be set to `False`.'
        )

        assert str(excinfo.value) == expected_error

    def test_destroy_on_success(
        self,
        dcos_cluster: Cluster,
        existing_cluster_backend: ClusterBackend,
    ) -> None:
        """
        If `destroy_on_success` is set to `True` an error is raised.
        """
        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=existing_cluster_backend,
                masters=len(dcos_cluster.masters),
                agents=len(dcos_cluster.agents),
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=False,
                destroy_on_success=True,
            ):
                pass  # pragma: no cover

        expected_error = (
            'The given cluster backend does not support being destroyed.'
            ' Therefore, `destroy_on_success` must be set to `False`.'
        )

        assert str(excinfo.value) == expected_error

    def test_files_to_copy_to_installer(
        self,
        dcos_cluster: Cluster,
        existing_cluster_backend: ClusterBackend,
    ) -> None:
        """
        If there are any files to copy to installers, an error is raised.
        """
        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=existing_cluster_backend,
                masters=len(dcos_cluster.masters),
                agents=len(dcos_cluster.agents),
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=False,
                destroy_on_success=False,
                files_to_copy_to_installer={Path('/foo'): Path('/bar')},
            ):
                pass  # pragma: no cover

        expected_error = (
            'No files can be copied to the installer of an existing cluster. '
            'Therefore, `files_to_copy_to_installer` must be empty.'
        )

        assert str(excinfo.value) == expected_error

    def test_files_to_copy_to_masters(
        self,
        dcos_cluster: Cluster,
        existing_cluster_backend: ClusterBackend,
    ) -> None:
        """
        If there are any files to copy to masters, an error is raised.
        """
        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=existing_cluster_backend,
                masters=len(dcos_cluster.masters),
                agents=len(dcos_cluster.agents),
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=False,
                destroy_on_success=False,
                files_to_copy_to_masters={Path('/foo'): Path('/bar')},
            ):
                pass  # pragma: no cover

        expected_error = (
            'No files can be copied to the masters of an existing cluster at '
            'install time. '
            'Therefore, `files_to_copy_to_masters` must be empty.'
        )

        assert str(excinfo.value) == expected_error

    def test_extra_config(
        self,
        dcos_cluster: Cluster,
        existing_cluster_backend: ClusterBackend,
    ) -> None:
        """
        If `extra_config` is not empty, an error is raised.
        """
        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=existing_cluster_backend,
                masters=len(dcos_cluster.masters),
                agents=len(dcos_cluster.agents),
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=False,
                destroy_on_success=False,
                extra_config={'foo': 'bar'},
            ):
                pass  # pragma: no cover

        expected_error = (
            'Nodes are already configured. '
            'Therefore, `extra_config` must be empty.'
        )

        assert str(excinfo.value) == expected_error

    def test_installer_file(
        self,
        dcos_cluster: Cluster,
        oss_artifact: Path,
        existing_cluster_backend: ClusterBackend,
    ) -> None:
        """
        If an installer file is given, an error is raised.
        """
        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=existing_cluster_backend,
                generate_config_path=oss_artifact,
                masters=len(dcos_cluster.masters),
                agents=len(dcos_cluster.agents),
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=False,
                destroy_on_success=False,
            ):
                pass  # pragma: no cover

        expected_error = (
            'Cluster already exists with DC/OS installed. '
            'Therefore, `generate_config_path` must be `None`.'
        )

        assert str(excinfo.value) == expected_error

    def test_mismatched_masters(
        self,
        dcos_cluster: Cluster,
        existing_cluster_backend: ClusterBackend,
    ) -> None:
        """
        If `masters` differs from the number of masters an error is raised.
        """
        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=existing_cluster_backend,
                generate_config_path=None,
                masters=len(dcos_cluster.masters) + 2,
                agents=len(dcos_cluster.agents),
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=False,
                destroy_on_success=False,
            ):
                pass  # pragma: no cover

        expected_error = (
            'The number of master nodes is `1`. '
            'Therefore, `masters` must be set to `1`.'
        )

        assert str(excinfo.value) == expected_error

    def test_mismatched_agents(
        self,
        dcos_cluster: Cluster,
        existing_cluster_backend: ClusterBackend,
    ) -> None:
        """
        If `agents` differs from the number of agents an error is raised.
        """
        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=existing_cluster_backend,
                generate_config_path=None,
                masters=len(dcos_cluster.masters),
                agents=len(dcos_cluster.agents) + 1,
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=False,
                destroy_on_success=False,
            ):
                pass  # pragma: no cover

        expected_error = (
            'The number of agent nodes is `1`. '
            'Therefore, `agents` must be set to `1`.'
        )

        assert str(excinfo.value) == expected_error

    def test_mismatched_public_agents(
        self,
        dcos_cluster: Cluster,
        existing_cluster_backend: ClusterBackend,
    ) -> None:
        """
        If `public_agents` differs from the number of public agents an error is
        raised.
        """
        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=existing_cluster_backend,
                generate_config_path=None,
                masters=len(dcos_cluster.masters),
                agents=len(dcos_cluster.agents),
                public_agents=len(dcos_cluster.public_agents) + 1,
                destroy_on_error=False,
                destroy_on_success=False,
            ):
                pass  # pragma: no cover

        expected_error = (
            'The number of public agent nodes is `1`. '
            'Therefore, `public_agents` must be set to `1`.'
        )

        assert str(excinfo.value) == expected_error
