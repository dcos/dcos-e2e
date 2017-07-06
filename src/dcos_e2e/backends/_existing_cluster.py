"""
Helpers for interacting with existing clusters.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Set

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
        generate_config_path: Optional[Path],
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

        if generate_config_path is not None:
            message = (
                'Cluster already exists with DC/OS installed. '
                'Therefore, `generate_config_path` must be `None`.'
            )
            raise ValueError(message)

        if masters != len(self._masters):
            message = (
                'The number of master nodes is `1`. '
                'Therefore, `masters` must be set to `1`.'
            )
            raise ValueError(message)

        if agents != len(self._agents):
            message = (
                'The number of agent nodes is `1`. '
                'Therefore, `agents` must be set to `1`.'
            )
            raise ValueError(message)

        if public_agents != len(self._public_agents):
            message = (
                'The number of public agent nodes is `1`. '
                'Therefore, `public_agents` must be set to `1`.'
            )
            raise ValueError(message)

        if extra_config not in (None, {}):
            message = (
                'Nodes are already configured. '
                'Therefore, `extra_config` must be empty.'
            )
            raise ValueError(message)

        if files_to_copy_to_installer != {}:
            message = (
                'No files can be copied to the installer of an existing '
                'cluster. '
                'Therefore, `files_to_copy_to_installer` must be empty.'
            )
            raise ValueError(message)

        if files_to_copy_to_masters != {}:
            message = (
                'No files can be copied to the masters of an existing cluster '
                'at install time. '
                'Therefore, `files_to_copy_to_masters` must be empty.'
            )
            raise ValueError(message)

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
