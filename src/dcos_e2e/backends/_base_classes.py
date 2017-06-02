"""
Abstract base classes.
"""

import abc
from pathlib import Path
from typing import Any, Dict, Optional, Set, Type

from .._common import Node


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
        extra_config: Dict[str, Any],
        custom_ca_key: Optional[Path],
        log_output_live: bool,
        files_to_copy_to_installer: Dict[Path, Path],
        cluster_backend: 'ClusterBackend',
    ) -> None:
        """
        Create a DC/OS cluster with the given `cluster_backend`.
        """

    @abc.abstractmethod
    def postflight(self) -> None:
        """
        Wait for nodes to be ready to run tests against.
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

    @property
    @abc.abstractmethod
    def superuser_username(self) -> str:
        """
        Return the original username of the superuser on the cluster.
        This may be outdated in that the username can change without this
        property changing.
        """

    @property
    @abc.abstractmethod
    def superuser_password(self) -> str:
        """
        Return the original password of the superuser on the cluster.
        This may be outdated in that the password can change without this
        property changing.
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
