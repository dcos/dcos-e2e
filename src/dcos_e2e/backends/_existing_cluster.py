"""
Helpers for interacting with existing clusters.
"""

from pathlib import Path
from typing import Any, Dict, Set

from dcos_e2e.backends._base_classes import ClusterBackend, ClusterManager
from dcos_e2e.node import Node


class Existing_Cluster(ClusterBackend):
    """
    A record of an existing DC/OS cluster.
    """

    def __init__(
        self,
        masters: Set[Node],
        agents: Set[Node],
        public_agents: Set[Node],
    ) -> None:
        """
        XXX
        """
        self.masters = masters
        self.agents = agents
        self.public_agents = public_agents


class Existing_Cluster_Manager(ClusterManager):
    """
    A record of a DC/OS cluster.
    """

    def __init__(  # pylint: disable=super-init-not-called
        self,
        generate_config_path: Path,
        masters: int,
        agents: int,
        public_agents: int,
        extra_config: Dict[str, Any],
        log_output_live: bool,
        files_to_copy_to_installer: Dict[Path, Path],
        files_to_copy_to_masters: Dict[Path, Path],
        cluster_backend: Existing_Cluster,
    ) -> None:
        """
        XXX
        """
        self._masters = cluster_backend.masters
        self._agents = cluster_backend.agents
        self._public_agents = cluster_backend.public_agents

        if not 1 == 2:
            pass

    @property
    def masters(self) -> Set[Node]:
        """
        Return all DC/OS master ``Node``s.
        """
        return self._masters

    @property
    def agents(self) -> Set[Node]:
        """
        Return all DC/OS agent ``Node``s.
        """
        return self._agents

    @property
    def public_agents(self) -> Set[Node]:
        """
        Return all DC/OS public agent ``Node``s.
        """
        return self._public_agents
