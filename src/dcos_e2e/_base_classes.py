import abc
from typing import Type


class ClusterImplementor(abc.ABC):
    """
    Cluster implementor base class.
    """


class ClusterBackend(abc.ABC):
    """
    Cluster Backend base class.
    """

    @abc.abstractmethod
    @property
    def cluster_cls(self) -> Type[ClusterImplementor]:
        pass
