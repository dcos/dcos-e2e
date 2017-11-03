"""
Classes to allow backend-specific configuration for cluster backend types.
"""

from ._base_classes import ClusterBackend, ClusterManager
from ._dcos_docker import Docker
from ._existing_cluster import ExistingCluster

__all__ = [
    'ClusterBackend',
    'ClusterManager',
    'Docker',
    'ExistingCluster',
]
