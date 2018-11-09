"""
Top level CLI commands.
"""

from .minidcos import minidcos
from .dcos_docker import dcos_docker
from .dcos_aws import dcos_aws
from .dcos_vagrant import dcos_vagrant

__all__ = [
    'minidcos',
]
