"""
Helpers for interacting with existing clusters.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Set, Type

from dcos_e2e.backends._base_classes import ClusterBackend, ClusterManager
from dcos_e2e.node import Node


class ExistingCluster(ClusterBackend):
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
        Create a record of an existing cluster backend for use by a cluster
        manager.
        """
        self.masters = masters
        self.agents = agents
        self.public_agents = public_agents

    @property
    def cluster_cls(self) -> Type['ExistingClusterManager']:
        """
        Return the `ClusterManager` class to use to create and manage a
        cluster.
        """
        return ExistingClusterManager


class ExistingClusterManager(ClusterManager):
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
        cluster_backend: ExistingCluster,
    ) -> None:
        """
        Create a manager for an existing DC/OS cluster.

        Args:
            generate_config_path: The path to a build artifact to install.
                This must be `None` as the cluster already exists.
            masters: The number of master nodes to create.
                This must match the number of masters in `cluster_backend`.
            agents: The number of agent nodes to create.
                This must match the number of agents in `cluster_backend`.
            public_agents: The number of public agent nodes to create.
                This must match the number of public agents in
                `cluster_backend`.
            extra_config: This dictionary can contain extra installation
                configuration variables. However, as the cluster already
                exists, there may not be
            log_output_live: If `True`, log output of subprocesses live.
                If `True`, stderr is merged into stdout in the return value.
            files_to_copy_to_installer: A mapping of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS. As the cluster
                already exists, there can be no paths given.
            files_to_copy_to_masters: A mapping of host paths to paths on the
                master nodes. These are files to copy from the host to
                the master nodes before installing DC/OS. As the cluster
                already exists, there can be no paths given.
            cluster_backend: Details of the specific existing cluster backend
                to use.

        Raises:
            ValueError: See `Args` for invalid arguments.
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

    def destroy(self) -> None:
        """
        Destroying an existing cluster is the responsibility of the caller.

        Raises: NotImplementedError when called.
        """
        raise NotImplementedError
