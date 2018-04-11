"""
Supported distributions for DC/OS.

In Python 3.6 this can use `enum.auto()`.
"""

from enum import Enum


class Distribution(Enum):
    """
    Supported distributions for DC/OS.
    """

    CENTOS_7 = 1
    COREOS = 2
    UBUNTU_16_04 = 3
