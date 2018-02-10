"""
Supported Docker storage drivers.
"""

from enum import Enum, auto


class DockerStorageDriver(Enum):
    """
    Supported Docker storage drivers.
    """

    AUFS = auto()
    OVERLAY = auto()
    OVERLAY_2 = auto()
