"""
Classes to allow backend-specific configuration for cluster backend types.
"""

from ._aws import AWS
from ._base_classes import ClusterBackend, ClusterManager
from ._docker import Docker
from ._vagrant import Vagrant

__all__ = [
    'ClusterBackend',
    'ClusterManager',
    'AWS',
    'Docker',
    'Vagrant',
]
