"""
Tools for interacting with DC/OS installers.
"""

from .artifact_utils import get_dcos_installer_details, DCOSVariant

from ._version import get_versions
__version__ = get_versions()['version']  # type: ignore
del get_versions

__all__ = [
    'DCOSVariant',
    'get_dcos_installer_details',
]
