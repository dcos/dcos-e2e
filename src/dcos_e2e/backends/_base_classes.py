"""
Abstract base classes.
"""

import abc
from pathlib import Path
from typing import Any, Dict, Set, Type

from ..node import Node


class ClusterManager(abc.ABC):
    """
    Cluster manager base class.
    """

    @abc.abstractmethod
    def __init__(
        self,
        generate_config_path: Path,
        masters: int,
        agents: int,
        public_agents: int,
        extra_config: Dict[str, Any],
        log_output_live: bool,
        files_to_copy_to_installer: Dict[Path, Path],
        files_to_copy_to_masters: Dict[Path, Path],
        cluster_backend: 'ClusterBackend',
    ) -> None:
        """
        Create a DC/OS cluster with the given `cluster_backend`.

        Args:
            generate_config_path: The path to a build artifact to install.
            masters: The number of master nodes to create.
            agents: The number of agent nodes to create.
            public_agents: The number of public agent nodes to create.
            extra_config: Implementations may come with a "base"
                configuration. This dictionary can contain extra installation
                configuration variables.
            log_output_live: If `True`, log output of subprocesses live.
                If `True`, stderr is merged into stdout in the return value.
            files_to_copy_to_installer: A mapping of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
            files_to_copy_to_masters: A mapping of host paths to paths on the
                master nodes. These are files to copy from the host to
                the master nodes before installing DC/OS.
            cluster_backend: Details of the specific DC/OS Docker backend to
                use.
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
        Return all DC/OS master ``Node``s.
        """

    @property
    @abc.abstractmethod
    def agents(self) -> Set[Node]:
        """
        Return all DC/OS agent ``Node``s.
        """

    @property
    @abc.abstractmethod
    def public_agents(self) -> Set[Node]:
        """
        Return all DC/OS public agent ``Node``s.
        """


class ClusterBackend(abc.ABC):
    """
    Cluster backend base class.
    """

    @property
    @abc.abstractmethod
    def cluster_cls(self) -> Type[ClusterManager]:
        """
        Return the `ClusterManager` class to use to create and manage a
        cluster.
        """
