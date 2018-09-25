"""
Custom exceptions.
"""


class DCOSTimeoutError(Exception):
    """
    Raised if DC/OS does not become ready within a given time boundary.
    """
