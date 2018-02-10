"""
Supported Docker storage drivers.

In Python 3.6 this can use `enum.auto()`.
"""

from enum import Enum


class DockerStorageDriver(Enum):
    """
    Supported Docker storage drivers.
    """

    AUFS = 1
    OVERLAY = 2
    OVERLAY_2 = 3
