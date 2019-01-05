"""
Tools for interacting with DC/OS installers.
"""

from ._version import get_versions
from .artifact_utils import DCOSVariant, get_dcos_installer_details

__version__ = get_versions()['version']  # type: ignore
del get_versions

__all__ = [
    'DCOSVariant',
    'get_dcos_installer_details',
]
