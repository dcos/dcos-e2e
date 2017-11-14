"""
Helpers for interacting with existing clusters.
"""

from pathlib import Path
from typing import Any, Dict, Set, Type

from dcos_e2e.backends._base_classes import ClusterBackend, ClusterManager
from dcos_e2e.node import Node


class ExistingCluster(ClusterBackend):
    """
    A record of an existing DC/OS cluster backend.
    """

    def __init__(
        self,
        masters: Set[Node],
        agents: Set[Node],
        public_agents: Set[Node],
        default_ssh_user: str,
    ) -> None:
        """
        Create a record of an existing cluster backend for use by a cluster
        manager.
        """
        self.masters = masters
        self.agents = agents
        self.public_agents = public_agents
        self._default_ssh_user = default_ssh_user

    @property
    def cluster_cls(self) -> Type['ExistingClusterManager']:
        """
        Return the `ClusterManager` class to use to create and manage a
        cluster.
        """
        return ExistingClusterManager

    @property
    def default_ssh_user(self) -> str:
        """
        Return the default SSH user for this backend.
        """
        return self._default_ssh_user


class ExistingClusterManager(ClusterManager):
    """
    A record of a DC/OS cluster.
    """

    def __init__(  # pylint: disable=super-init-not-called
        self,
        masters: int,
        agents: int,
        public_agents: int,
        files_to_copy_to_installer: Dict[Path, Path],
        cluster_backend: ExistingCluster,
    ) -> None:
        """
        Create a manager for an existing DC/OS cluster.

        Args:
            masters: The number of master nodes to create.
                This must match the number of masters in `cluster_backend`.
            agents: The number of agent nodes to create.
                This must match the number of agents in `cluster_backend`.
            public_agents: The number of public agent nodes to create.
                This must match the number of public agents in
                `cluster_backend`.
            files_to_copy_to_installer: A mapping of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS. As the cluster
                already exists, there can be no paths given.
            cluster_backend: Details of the specific existing cluster backend
                to use.

        Raises:
            ValueError: See `Args` for invalid arguments.
        """
        self._masters = cluster_backend.masters
        self._agents = cluster_backend.agents
        self._public_agents = cluster_backend.public_agents

        if masters != len(self._masters):
            message = (
                'The number of master nodes is {len_masters}. '
                'Therefore, masters must be set to {len_masters}.'
            ).format(len_masters=len(self._masters))
            raise ValueError(message)

        if agents != len(self._agents):
            message = (
                'The number of agent nodes is {len_agents}. '
                'Therefore, agents must be set to {len_agents}.'
            ).format(len_agents=len(self._agents))
            raise ValueError(message)

        if public_agents != len(self._public_agents):
            message = (
                'The number of public agent nodes is {len_public_agents}. '
                'Therefore, public_agents must be set to {len_public_agents}.'
            ).format(len_public_agents=len(self._public_agents))
            raise ValueError(message)

        if files_to_copy_to_installer != {}:
            message = (
                'No files can be copied to the installer of an existing '
                'cluster. '
                'Therefore, `files_to_copy_to_installer` must be empty.'
            )
            raise ValueError(message)

    def install_dcos_from_url(
        self,
        build_artifact: str,
        extra_config: Dict[str, Any],
        log_output_live: bool,
    ) -> None:
        """
        Raises:
            NotImplementedError: Raises `NotImplementedError` because it
                is assumed that clusters created with the ExistingCluster
                backend already have an installed instance of DC/OS
                running on them.
        """
        message = (
            'The ExistingCluster backend does not support installing '
            'DC/OS because it is assumed that an instance of DC/OS is '
            'already installed and running on the cluster.'
        )
        raise NotImplementedError(message)

    def install_dcos_from_path(
        self,
        build_artifact: Path,
        extra_config: Dict[str, Any],
        log_output_live: bool,
    ) -> None:
        """
        Raises:
            NotImplementedError: Raises `NotImplementedError` because it
                is assumed that clusters created with the ExistingCluster
                backend already have an installed instance of DC/OS
                running on them.
        """
        message = (
            'The ExistingCluster backend does not support installing '
            'DC/OS because it is assumed that an instance of DC/OS is '
            'already installed and running on the cluster.'
        )
        raise NotImplementedError(message)

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
