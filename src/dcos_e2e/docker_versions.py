"""
Supported versions of Docker for DC/OS.

See
https://docs.mesosphere.com/1.10/installing/oss/custom/system-requirements/#docker

In Python 3.6 this can use `enum.auto()`.
"""

from enum import Enum


class DockerVersion(Enum):
    """
    Supported versions of Docker for DC/OS.
    """

    v1_13_1 = 1
    v1_11_2 = 2
