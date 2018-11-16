"""
Top level CLI commands.
"""

from .dcos_aws import dcos_aws
from .dcos_docker import dcos_docker
from .dcos_vagrant import dcos_vagrant
from .minidcos import minidcos

__all__ = [
    'dcos_aws',
    'dcos_docker',
    'dcos_vagrant',
    'minidcos',
]
