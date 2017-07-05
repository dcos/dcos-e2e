"""
Tests for the DC/OS Docker backend.
"""

import uuid
from pathlib import Path
from typing import Optional

import pytest

from dcos_e2e.backends import DCOS_Docker
from dcos_e2e.cluster import Cluster


class TestBadParameters:
    """
    Tests for unexpected parameter values.
    """

    @pytest.mark.parametrize('no_such_path', [None, str(uuid.uuid4())])
    def test_no_installer_file(self, no_such_path: Optional[Path]) -> None:
        """
        If no file exists at the given `generate_config_path`, a `ValueError`
        is raised.
        """
        with pytest.raises(ValueError):
            with Cluster(
                cluster_backend=DCOS_Docker(),
                generate_config_path=no_such_path,
            ):
                pass  # pragma: no cover
