"""
Tests for the DC/OS Docker backend.
"""

import uuid
from pathlib import Path

import pytest
# See https://github.com/PyCQA/pylint/issues/1536 for details on why the errors
# are disabled.
from py.path import local  # pylint: disable=no-name-in-module, import-error

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster


class TestBadParameters:
    """
    Tests for unexpected parameter values.
    """

    def test_no_installer_file(self, cluster_backend: ClusterBackend) -> None:
        """
        If no file exists at the given `generate_config_path`, a `ValueError`
        is raised.
        """
        with pytest.raises(ValueError):
            with Cluster(
                cluster_backend=cluster_backend,
                generate_config_path=Path(str(uuid.uuid4)),
                agents=0,
                public_agents=0,
            ):
                pass  # pragma: no cover
