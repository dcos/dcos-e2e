"""
Supported distributions for DC/OS.
"""

from enum import Enum, auto

# TODO investigate auto() value


class Distribution(Enum):
    """
    Supported distributions for DC/OS.
    """

    CENTOS_7 = auto()
    UBUNTU_16_04 = auto()
    COREOS = auto()
    FEDORA_23 = auto()
    DEBIAN_8 = auto()
