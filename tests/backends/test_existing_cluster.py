"""
Tests for the existing cluster backend.
"""

from pathlib import Path
from typing import Iterator

import pytest

from dcos_e2e.backends import ClusterBackend, Docker, ExistingCluster
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
        backend = Docker()
        with Cluster(
            cluster_backend=backend,
            masters=1,
            agents=1,
            public_agents=1,
            destroy_on_success=False,
        ) as cluster:
            cluster.install_dcos_from_path(oss_artifact)
            (master, ) = cluster.masters
            (agent, ) = cluster.agents
            (public_agent, ) = cluster.public_agents

            existing_cluster = ExistingCluster(
                masters=cluster.masters,
                agents=cluster.agents,
                public_agents=cluster.public_agents,
                default_ssh_user=backend.default_ssh_user
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
                    user=duplicate_cluster.default_ssh_user
                )
                duplicate_agent.run(
                    args=['touch', 'example_agent_file'],
                    user=duplicate_cluster.default_ssh_user
                )
                duplicate_public_agent.run(
                    args=['touch', 'example_public_agent_file'],
                    user=duplicate_cluster.default_ssh_user
                )

                master.run(
                    args=['test', '-f', 'example_master_file'],
                    user=duplicate_cluster.default_ssh_user
                )
                agent.run(
                    args=['test', '-f', 'example_agent_file'],
                    user=duplicate_cluster.default_ssh_user
                )
                public_agent.run(
                    args=['test', '-f', 'example_public_agent_file'],
                    user=duplicate_cluster.default_ssh_user
                )

            with pytest.raises(NotImplementedError):
                duplicate_cluster.destroy()

            cluster.destroy()


class TestBadParameters:
    """
    Tests for unexpected parameter values.
    """

    @pytest.fixture(scope='module')
    def dcos_cluster(self, oss_artifact: Path) -> Iterator[Cluster]:
        """
        Return a `Cluster`.

        This is module scoped as we do not intend to modify the cluster.
        """
        with Cluster(
            cluster_backend=Docker(),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            cluster.install_dcos_from_path(oss_artifact)
            yield cluster

    @pytest.fixture()
    def existing_cluster_backend(
        self, dcos_cluster: Cluster
    ) -> ClusterBackend:
        """
        Return an `ExistingCluster` with the nodes from `dcos_cluster`. """
        return ExistingCluster(
            masters=dcos_cluster.masters,
            agents=dcos_cluster.agents,
            public_agents=dcos_cluster.public_agents,
            default_ssh_user=dcos_cluster.default_ssh_user
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
                masters=len(dcos_cluster.masters) + 2,
                agents=len(dcos_cluster.agents),
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=False,
                destroy_on_success=False,
            ):
                pass  # pragma: no cover

        expected_error = (
            'The number of master nodes is {len_masters}. '
            'Therefore, masters must be set to {len_masters}.'
        ).format(len_masters=len(dcos_cluster.masters))

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
                masters=len(dcos_cluster.masters),
                agents=len(dcos_cluster.agents) + 1,
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=False,
                destroy_on_success=False,
            ):
                pass  # pragma: no cover

        expected_error = (
            'The number of agent nodes is {len_agents}. '
            'Therefore, agents must be set to {len_agents}.'
        ).format(len_agents=len(dcos_cluster.agents))

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
                masters=len(dcos_cluster.masters),
                agents=len(dcos_cluster.agents),
                public_agents=len(dcos_cluster.public_agents) + 1,
                destroy_on_error=False,
                destroy_on_success=False,
            ):
                pass  # pragma: no cover

        expected_error = (
            'The number of public agent nodes is {len_public_agents}. '
            'Therefore, public_agents must be set to {len_public_agents}.'
        ).format(len_public_agents=len(dcos_cluster.public_agents))

        assert str(excinfo.value) == expected_error


class TestUnsupportedInstallationMethods:
    """
    Tests for unsupported installation methods.
    """

    @pytest.fixture(scope='module')
    def dcos_cluster(self, oss_artifact: Path) -> Iterator[Cluster]:
        """
        Return a `Cluster`.

        This is module scoped as we do not intend to modify the cluster.
        """
        with Cluster(
            cluster_backend=Docker(),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            cluster.install_dcos_from_path(oss_artifact)
            yield cluster

    @pytest.fixture()
    def existing_cluster_backend(
        self, dcos_cluster: Cluster
    ) -> ClusterBackend:
        """
        Return an `ExistingCluster` with the nodes from `dcos_cluster`. """
        return ExistingCluster(
            masters=dcos_cluster.masters,
            agents=dcos_cluster.agents,
            public_agents=dcos_cluster.public_agents,
            default_ssh_user=dcos_cluster.default_ssh_user
        )

    def test_install_dcos_from_url(
        self,
        dcos_cluster: Cluster,
        oss_artifact_url: str,
        existing_cluster_backend: ClusterBackend,
    ) -> None:
        """
        If `install_dcos_from_url` is called on a `Cluster` created with
        the `ExistingCluster` backend, a `NotImplementedError` is raised.
        """
        with pytest.raises(NotImplementedError) as excinfo:
            with Cluster(
                cluster_backend=existing_cluster_backend,
                masters=len(dcos_cluster.masters),
                agents=len(dcos_cluster.agents),
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=False,
                destroy_on_success=False,
            ) as cluster:
                cluster.install_dcos_from_url(oss_artifact_url)

        expected_error = (
            'The ExistingCluster backend does not support installing '
            'DC/OS because it is assumed that an instance of DC/OS is '
            'already installed and running on the cluster.'
        )

        assert str(excinfo.value) == expected_error

    def test_install_dcos_from_path(
        self,
        dcos_cluster: Cluster,
        oss_artifact: Path,
        existing_cluster_backend: ClusterBackend,
    ) -> None:
        """
        If `install_dcos_from_path` is called on a `Cluster` created with
        the `ExistingCluster` backend, a `NotImplementedError` is raised.
        """
        with pytest.raises(NotImplementedError) as excinfo:
            with Cluster(
                cluster_backend=existing_cluster_backend,
                masters=len(dcos_cluster.masters),
                agents=len(dcos_cluster.agents),
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=False,
                destroy_on_success=False,
            ) as cluster:
                cluster.install_dcos_from_path(oss_artifact)

        expected_error = (
            'The ExistingCluster backend does not support installing '
            'DC/OS because it is assumed that an instance of DC/OS is '
            'already installed and running on the cluster.'
        )

        assert str(excinfo.value) == expected_error
