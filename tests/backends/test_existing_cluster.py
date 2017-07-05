"""
Tests for the existing cluster backend.
"""

from pathlib import Path

"""
XXX
"""

import pytest

from dcos_e2e.backends import DCOS_Docker, Existing_Cluster
from dcos_e2e.cluster import Cluster

# TODO:
# - make node public
# - fill in tests
#  - destroy on error must be false
# files to copy to installer / master must be empty
# document Node and new backend
# Separate making Node public

class TestExistingCluster:
    """
    Tests for creating a `Cluster` with the `Existing_Cluster` backend.
    """

    def test_existing_cluster(self, oss_artifact: Path) -> None:
        """
        It is possible to create a cluster from existing nodes.
        """
        pass


class TestBadParameters:
    """
    Tests for unexpected parameter values.
    """

    def test_installer_file(self, oss_artifact: Path) -> None:
        """
        If an installer file is given, an error is raised.
        """
        num_masters = 1
        num_agents = 0
        num_public_agents = 0

        with Cluster(
            cluster_backend=DCOS_Docker(),
            generate_config_path=oss_artifact,
            masters=num_masters,
            agents=num_agents,
            public_agents=num_public_agents,
        ) as cluster:
            existing_cluster = Existing_Cluster(
                masters=cluster.masters,
                agents=cluster.agents,
                public_agents=cluster.public_agents,
            )

            with pytest.raises(ValueError) as excinfo:
                with Cluster(
                    cluster_backend=existing_cluster,
                    generate_config_path=oss_artifact,
                    masters=num_masters,
                    agents=num_agents,
                    public_agents=num_public_agents,
                ):
                    pass  # pragma: no cover

            expected_error = (
                'Cluster already exists with DC/OS installed. '
                '`generate_config_path` must be `None`.'
            )

            assert excinfo.value == expected_error

    def test_mismatched_node_numbers(self, oss_artifact: Path) -> None:
        """
        If an installer file is given, an error is raised.
        """
        num_masters = 1
        num_agents = 0
        num_public_agents = 0

        with Cluster(
            cluster_backend=DCOS_Docker(),
            generate_config_path=oss_artifact,
            masters=num_masters,
            agents=num_agents,
            public_agents=num_public_agents,
        ) as cluster:
            existing_cluster = Existing_Cluster(
                masters=cluster.masters,
                agents=cluster.agents,
                public_agents=cluster.public_agents,
            )

            with pytest.raises(ValueError) as excinfo:
                with Cluster(
                    cluster_backend=existing_cluster,
                    generate_config_path=None,
                    masters=num_masters + 1,
                    agents=num_agents,
                    public_agents=num_public_agents,
                ):
                    pass  # pragma: no cover

            expected_error = (
                'The number of master nodes is `1`. '
                'Therefore `masters` must be set to `1`.'
            )

            assert excinfo.value == expected_error

            with pytest.raises(ValueError) as excinfo:
                with Cluster(
                    cluster_backend=existing_cluster,
                    generate_config_path=None,
                    masters=num_masters,
                    agents=num_agents + 1,
                    public_agents=num_public_agents,
                ):
                    pass  # pragma: no cover

            expected_error = (
                'The number of agent nodes is `0`. '
                'Therefore `agents` must be set to `0`.'
            )

            assert excinfo.value == expected_error

            with pytest.raises(ValueError) as excinfo:
                with Cluster(
                    cluster_backend=existing_cluster,
                    generate_config_path=None,
                    masters=num_masters,
                    agents=num_agents,
                    public_agents=num_public_agents + 1,
                ):
                    pass  # pragma: no cover

            expected_error = (
                'The number of public agent nodes is `0`. '
                'Therefore `public_agents` must be set to `0`.'
            )

            assert excinfo.value == expected_error
