"""
Classes to allow backend-specific configuration for cluster backend types.
"""

from ._base_classes import ClusterBackend
from ._dcos_docker import DCOS_Docker

__all__ = ['ClusterBackend', 'DCOS_Docker']
