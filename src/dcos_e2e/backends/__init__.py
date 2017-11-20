"""
Classes to allow backend-specific configuration for cluster backend types.
"""

from ._base_classes import ClusterBackend, ClusterManager
from ._docker import Docker
from ._existing_cluster import ExistingCluster as _ExistingCluster

__all__ = [
    'ClusterBackend',
    'ClusterManager',
    'Docker',
    '_ExistingCluster',
]
