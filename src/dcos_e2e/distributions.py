"""
Supported distributions for DC/OS.
"""

from enum import Enum
# TODO investigate auto() value

class Distribution(Enum):
    """
    Supported distributions for DC/OS.
    """

    CENTOS_7 = 1
    UBUNTU_16_04 = 2
    COREOS = 3
    FEDORA_23 = 4
    DEBIAN_8 = 5
