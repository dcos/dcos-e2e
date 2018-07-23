"""
Abstract base classes for cluster backends.
"""

import abc
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Type

from ..node import Node


class ClusterManager(abc.ABC):
    """
    Cluster manager base class.
    """

    @abc.abstractmethod
    def __init__(
        self,
        masters: int,
        agents: int,
        public_agents: int,
        files_to_copy_to_installer: List[Tuple[Path, Path]],
        cluster_backend: 'ClusterBackend',
    ) -> None:
        """
        Create a DC/OS cluster with the given ``cluster_backend``.

        Args:
            masters: The number of master nodes to create.
            agents: The number of agent nodes to create.
            public_agents: The number of public agent nodes to create.
            files_to_copy_to_installer: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
            cluster_backend: Details of the specific DC/OS Docker backend to
                use.
        """

    @abc.abstractmethod
    def install_dcos_from_url_with_bootstrap_node(
        self,
        build_artifact: str,
        dcos_config: Dict[str, Any],
        log_output_live: bool,
    ) -> None:
        """
        Install DC/OS from a URL with a bootstrap node.

        If a method which implements this abstract method raises a
        ``NotImplementedError``, users of the backend can still install DC/OS
        from a URL in an inefficient manner.

        Args:
            build_artifact: The URL string to a build artifact to install DC/OS
                from.
            dcos_config: The DC/OS configuration to use.
            log_output_live: If ``True``, log output of the installation live.
        """

    @abc.abstractmethod
    def install_dcos_from_path_with_bootstrap_node(
        self,
        build_artifact: Path,
        dcos_config: Dict[str, Any],
        log_output_live: bool,
    ) -> None:
        """
        Install DC/OS from a build artifact passed as a file system `Path`.

        If a method which implements this abstract method raises a
        ``NotImplementedError``, users of the backend can still install DC/OS
        from a path in an inefficient manner.

        Args:
            build_artifact: The path to a build artifact to install DC/OS from.
            dcos_config: The DC/OS configuration to use.
            log_output_live: If ``True``, log output of the installation live.
        """

    @abc.abstractmethod
    def destroy_node(self, node: Node) -> None:
        """
        Destroy a node in the cluster.
        """

    @abc.abstractmethod
    def destroy(self) -> None:
        """
        Destroy all nodes in the cluster.
        """

    @property
    @abc.abstractmethod
    def masters(self) -> Set[Node]:
        """
        Return all DC/OS master :class:`.node.Node` s.
        """

    @property
    @abc.abstractmethod
    def agents(self) -> Set[Node]:
        """
        Return all DC/OS agent :class:`.node.Node` s.
        """

    @property
    @abc.abstractmethod
    def public_agents(self) -> Set[Node]:
        """
        Return all DC/OS public agent :class:`.node.Node` s.
        """

    @property
    @abc.abstractmethod
    def base_config(self) -> Dict[str, Any]:
        """
        Return a base configuration for installing DC/OS OSS.

        This does not need to include the lists of IP addresses for each node
        type.
        """

    @property
    @abc.abstractmethod
    def ip_detect_path(self) -> Path:
        """
        Return the file system path to a valid ``ip-detect`` script.

        If executed on a node, the script that this path points to returns
        the current private IP address of this node.
        """


class ClusterBackend(abc.ABC):
    """
    Cluster backend base class.
    """

    @property
    @abc.abstractmethod
    def cluster_cls(self) -> Type[ClusterManager]:
        """
        Return the :class:`ClusterManager` class to use to create and manage a
        cluster.
        """
