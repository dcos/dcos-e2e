"""
Top level CLI commands.
"""

from .dcos_docker import dcos_docker
from .dcos_vagrant import dcos_vagrant

__all__ = [
    'dcos_docker',
    'dcos_vagrant',
]
