from pathlib import Path
from textwrap import dedent

from py.path import local  # pylint: disable=no-name-in-module, import-error

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Role


class TestCustomIPDetect:
    """
    Users can specify a custom ``ip-detect``.
    """

