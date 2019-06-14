"""
Custom exceptions.
"""


class DCOSNotInstalledError(Exception):
    """
    Raised if DC/OS is not installed on a node where it is expected.
    """


class DCOSTimeoutError(Exception):
    """
    Raised if DC/OS does not become ready within a given time boundary.
    """
