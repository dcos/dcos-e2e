"""
Tests for the existing cluster backend.
"""

from pathlib import Path

import pytest

from dcos_e2e.backends import DCOS_Docker, Existing_Cluster
from dcos_e2e.cluster import Cluster


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
        XXX
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

            with pytest.raises(ValueError):
                with Cluster(
                    cluster_backend=existing_cluster,
                    generate_config_path=oss_artifact,
                    masters=num_masters,
                    agents=num_agents,
                    public_agents=num_public_agents,
                ):
                    pass  # pragma: no cover
