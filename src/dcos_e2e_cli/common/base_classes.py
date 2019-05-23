"""
Abstract base classes for making CLIs.
"""

import abc
from typing import Any, Dict, Set

from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node


class ClusterRepresentation(abc.ABC):
    """
    A representation of a cluster.
    """

    @abc.abstractmethod
    def to_node(self, node_representation: Any) -> Node:
        """
        Return the ``Node`` that is represented.
        """

    @abc.abstractmethod
    def to_dict(self, node_representation: Any) -> Dict[str, str]:
        """
        Return information to be shown to users which is unique to this node.
        """

    @property
    @abc.abstractmethod
    def base_config(self) -> Dict[str, Any]:
        """
        Return a base configuration for installing DC/OS OSS.
        """

    @property
    @abc.abstractmethod
    def masters(self) -> Set[Any]:
        """
        All DC/OS master node representations.
        """

    @property
    @abc.abstractmethod
    def agents(self) -> Set[Any]:
        """
        All DC/OS agent node representations.
        """

    @property
    @abc.abstractmethod
    def public_agents(self) -> Set[Any]:
        """
        All DC/OS agent node representations.
        """

    @property
    @abc.abstractmethod
    def cluster(self) -> Cluster:
        """
        Return a ``Cluster`` constructed from the containers.
        """

    @abc.abstractmethod
    def destroy(self) -> None:
        """
        Destroy this cluster.
        """
