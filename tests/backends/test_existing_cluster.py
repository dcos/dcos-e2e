"""
Tests for the existing cluster backend.
"""

from pathlib import Path
from typing import Optional

import pytest

from dcos_e2e.backends import DCOS_Docker, Existing_Cluster
from dcos_e2e.cluster import Cluster


class TestExistingCluster:
    """
    Tests for creating a `Cluster` with the `Existing_Cluster` backend.
    """

    def test_existing_cluster(self):
        """
        It is possible to create a cluster from existing nodes.
        """
        pass


class TestBadParameters:
    """
    Tests for unexpected parameter values.
    """

    def test_no_installer_file(self) -> None:
        """
        If no file exists at the given `generate_config_path`, a `ValueError`
        is raised.
        """
        num_masters = 1
        num_agents = 2
        num_public_agents = 3

        no_such_path = Path('/')

        with Cluster(
            cluster_backend=DCOS_Docker(),
            generate_config_path=no_such_path,
            masters=num_masters,
            agents=num_agents,
            public_agents=num_public_agents,
        ) as cluster:
            existing_cluster = Existing_Cluster(
                masters=cluster.masters,
                agents=cluster.agents,
                public_agents=cluster.public_agents,
            )

            generate_config_path = Path('/')

            with pytest.raises(ValueError):
                with Cluster(
                    cluster_backend=existing_cluster,
                    generate_config_path=generate_config_path,
                ):
                    pass  # pragma: no cover
