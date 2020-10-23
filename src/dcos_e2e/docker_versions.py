"""
Supported versions of Docker for DC/OS.

See
https://docs.d2iq.com/mesosphere/dcos/2.1/installing/production/system-requirements/docker-centos/

In Python 3.6 this can use `enum.auto()`.
"""

from enum import Enum


class DockerVersion(Enum):
    """
    Supported versions of Docker for DC/OS.
    """

    v1_11_2 = 1
    v1_13_1 = 2
    v17_12_1_ce = 3
    v18_06_3_ce = 4
