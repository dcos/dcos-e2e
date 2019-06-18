"""
Helpers for interacting with existing clusters.
"""

from pathlib import Path
from typing import Any, Dict, Iterable, Set, Tuple, Type

from dcos_e2e.base_classes import ClusterBackend, ClusterManager
from dcos_e2e.node import Node, Output, Role


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

    @property
    def ip_detect_path(self) -> Path:  # pragma: no cover
        """
        Return the path to a ``ip-detect`` script.

        Raises:
            NotImplementedError: The ``ExistingCluster`` backend cannot
                be associated with a specific ``ip-detect`` script.
        """
        raise NotImplementedError

    @property
    def base_config(self) -> Dict[str, Any]:
        """
        Return a base configuration for installing DC/OS OSS.
        """
        return {}


class ExistingClusterManager(ClusterManager):
    """
    A record of a DC/OS cluster.
    """

    def __init__(  # pylint: disable=super-init-not-called
        self,
        masters: int,
        agents: int,
        public_agents: int,
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
            cluster_backend: Details of the specific existing cluster backend
                to use.
        """
        self._masters = cluster_backend.masters
        self._agents = cluster_backend.agents
        self._public_agents = cluster_backend.public_agents

    def install_dcos_from_url(
        self,
        dcos_installer: str,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        output: Output,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
    ) -> None:
        """
        Install DC/OS from a URL with a bootstrap node.

        Args:
            dcos_installer: The URL string to an installer to install DC/OS
                from.
            dcos_config: The DC/OS configuration to use.
            ip_detect_path: The ``ip-detect`` script to use for installing
                DC/OS.
            output: What happens with stdout and stderr.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
        """
        for nodes, role in (
            (self.masters, Role.MASTER),
            (self.agents, Role.AGENT),
            (self.public_agents, Role.PUBLIC_AGENT),
        ):
            for node in nodes:
                node.install_dcos_from_url(
                    dcos_installer=dcos_installer,
                    dcos_config=dcos_config,
                    ip_detect_path=ip_detect_path,
                    files_to_copy_to_genconf_dir=(
                        files_to_copy_to_genconf_dir
                    ),
                    role=role,
                    output=output,
                )

    def install_dcos_from_path(
        self,
        dcos_installer: Path,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        output: Output,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
    ) -> None:
        """
        Install DC/OS from an installer passed as a file system ``Path``.

        Args:
            dcos_installer: The path to an installer to install DC/OS from.
            dcos_config: The DC/OS configuration to use.
            ip_detect_path: The ``ip-detect`` script to use for installing
                DC/OS.
            output: What happens with stdout and stderr.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
        """
        for nodes, role in (
            (self.masters, Role.MASTER),
            (self.agents, Role.AGENT),
            (self.public_agents, Role.PUBLIC_AGENT),
        ):
            for node in nodes:
                node.install_dcos_from_path(
                    dcos_installer=dcos_installer,
                    dcos_config=dcos_config,
                    ip_detect_path=ip_detect_path,
                    files_to_copy_to_genconf_dir=(
                        files_to_copy_to_genconf_dir
                    ),
                    role=role,
                    output=output,
                )

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

    def destroy_node(self, node: Node) -> None:
        """
        Destroying an existing cluster node is the responsibility of the
        caller.

        Raises:
            NotImplementedError: When called.
        """
        raise NotImplementedError

    def destroy(self) -> None:
        """
        Destroying an existing cluster is the responsibility of the caller.

        Raises:
            NotImplementedError: When called.
        """
        raise NotImplementedError
