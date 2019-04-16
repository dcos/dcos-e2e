"""
Abstract base classes for cluster backends.
"""

import abc
from pathlib import Path
from typing import Any, Dict, Iterable, Set, Tuple, Type

from dcos_e2e.node import Node, Output


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
        cluster_backend: 'ClusterBackend',
    ) -> None:
        """
        Create a DC/OS cluster with the given ``cluster_backend``.

        Args:
            masters: The number of master nodes to create.
            agents: The number of agent nodes to create.
            public_agents: The number of public agent nodes to create.
            cluster_backend: Details of the specific DC/OS Docker backend to
                use.
        """

    @abc.abstractmethod
    def install_dcos_from_url(
        self,
        dcos_installer: str,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        output: Output,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
    ) -> None:
        """
        Install DC/OS from a URL.

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

    @abc.abstractmethod
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
        All DC/OS master :class:`.node.Node` s.
        """

    @property
    @abc.abstractmethod
    def agents(self) -> Set[Node]:
        """
        All DC/OS agent :class:`.node.Node` s.
        """

    @property
    @abc.abstractmethod
    def public_agents(self) -> Set[Node]:
        """
        All DC/OS public agent :class:`.node.Node` s.
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

    @property
    @abc.abstractmethod
    def ip_detect_path(self) -> Path:
        """
        Return the path to a backend specific ``ip-detect`` script.
        """

    @property
    @abc.abstractmethod
    def base_config(self) -> Dict[str, Any]:
        """
        Return a base configuration for installing DC/OS OSS.

        This does not need to include the lists of IP addresses for each node
        type.
        """
