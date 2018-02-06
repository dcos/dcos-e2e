"""
Supported Docker storage drivers.
"""

from enum import Enum


class DockerStorageDriver(Enum):
    """
    Supported Docker storage drivers.
    """

    AUFS = 1
    OVERLAY = 2
    OVERLAY_2 = 3
