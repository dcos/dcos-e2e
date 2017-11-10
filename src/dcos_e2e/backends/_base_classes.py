"""
Abstract base classes.
"""

import abc
from pathlib import Path
from typing import Any, Dict, Optional, Set, Type, Union

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
        files_to_copy_to_installer: Dict[Path, Path],
        cluster_backend: 'ClusterBackend',
    ) -> None:
        """
        Create a DC/OS cluster with the given `cluster_backend`.

        Args:
            masters: The number of master nodes to create.
            agents: The number of agent nodes to create.
            public_agents: The number of public agent nodes to create.
            files_to_copy_to_installer: A mapping of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
            cluster_backend: Details of the specific DC/OS Docker backend to
                use.
        """

    @abc.abstractmethod
    def install_dcos_from_url(
        self,
        build_artifact: str,
        extra_config: Dict[str, Any]),
        log_output_live: bool,
    ) -> None:
        """
        Stub for the DC/OS advanced installation method.

        Args:
            build_artifact: The URL string to a build artifact to install DC/OS
                from.
            extra_config: Implementations may come with a "base"
                configuration. This dictionary can contain extra installation
                configuration variables.
            log_output_live: If `True`, log output of the installation live.
                If `True`, stderr is merged into stdout in the return value.

        Raises:
            NotImplementedError: `NotImplementedError` because the Docker backend
                does not support the DC/OS advanced installation method.
        """
        message = (
            'This backend does not support the installation of DC/OS via build'
            'artifacts passed by URL string. This is because a more efficient '
            'installation method exists that uses a local build artifact.'
        )
        raise NotImplementedError(message)

    def install_dcos_from_path(
        self,
        build_artifact: str,
        extra_config: Dict[str, Any],
        log_output_live: bool,
    ) -> None:
        """
        Stub for a more efficient local DC/OS installation method.

        Args:
            build_artifact: The `Path`to a build artifact to install DC/OS from.
            extra_config: Implementations may come with a "base"
                configuration. This dictionary can contain extra installation
                configuration variables.
            log_output_live: If `True`, log output of the installation live.
                If `True`, stderr is merged into stdout in the return value.

        Raises:
            NotImplementedError: `NotImplementedError` because the Docker backend
                does not support the DC/OS advanced installation method.
        """
        message = (
            'This backend does not support the installation of DC/OS via local'
            'build artifacts. This is because a more efficient installation'
            'method exists that uses a remote build artifact.'
        )
        raise NotImplementedError(message)

    @abc.abstractmethod
    def destroy(self) -> None:
        """
        Destroy all nodes in the cluster.
        """
        message = (
            'The user is responsible for destroying the cluster.'
        )
        raise NotImplementedError(message)

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

    @property
    @abc.abstractmethod
    def supports_destruction(self) -> bool:
        """
        Return whether this backend supports being destroyed with a `destroy`
        method.
        """
        return False
    @property
    @abc.abstractmethod
    def default_ssh_user(self) -> str:
        """
        Return the default SSH user as a string.
        """
