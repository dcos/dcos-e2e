"""
Helpers for interacting with existing clusters.
"""

from pathlib import Path
from typing import Any, Dict, Iterable, Set, Tuple, Type

from dcos_e2e.node import Node

from ._base_classes import ClusterBackend, ClusterManager


class ExistingCluster(ClusterBackend):
    """
    A record of an existing DC/OS cluster backend.
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
        Return the :class:`dcos_e2e.backends.ClusterManager` class to use to
        create and manage a cluster.
        """
        return ExistingClusterManager


class ExistingClusterManager(ClusterManager):
    """
    A record of a DC/OS cluster.
    """

    def __init__(  # pylint: disable=super-init-not-called
        self,
        masters: int,
        agents: int,
        public_agents: int,
        files_to_copy_to_installer: Iterable[Tuple[Path, Path]],
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
            files_to_copy_to_installer: Ignored pairs of host paths to paths
                on the installer node.
            cluster_backend: Details of the specific existing cluster backend
                to use.
        """
        self._masters = cluster_backend.masters
        self._agents = cluster_backend.agents
        self._public_agents = cluster_backend.public_agents

    def install_dcos_from_url(
        self,
        build_artifact: str,
        extra_config: Dict[str, Any],
        log_output_live: bool,
    ) -> None:
        """
        Raises:
            NotImplementedError: It is assumed that clusters created with the
                :class:`ExistingCluster` backend already have an installed
                instance of DC/OS running on them.
        """
        raise NotImplementedError

    def install_dcos_from_path(
        self,
        build_artifact: Path,
        extra_config: Dict[str, Any],
        log_output_live: bool,
    ) -> None:
        """
        Raises:
            NotImplementedError: It is assumed that clusters created with the
                :class:`ExistingCluster` backend already have an installed
                instance of DC/OS running on them.
        """
        raise NotImplementedError

    @property
    def masters(self) -> Set[Node]:
        """
        Return all DC/OS master :class:`dcos_e2e.node.Node` s.
        """
        return self._masters

    @property
    def agents(self) -> Set[Node]:
        """
        Return all DC/OS agent :class:`dcos_e2e.node.Node` s.
        """
        return self._agents

    @property
    def public_agents(self) -> Set[Node]:
        """
        Return all DC/OS public agent :class:`dcos_e2e.node.Node` s.
        """
        return self._public_agents

    def destroy(self) -> None:
        """
        Destroying an existing cluster is the responsibility of the caller.

        Raises:
            NotImplementedError: When called.
        """
        raise NotImplementedError
