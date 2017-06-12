"""
Helpers for running tests with `pytest`.
"""

from pathlib import Path

import pytest

from dcos_e2e.backends import ClusterBackend, DCOS_Docker


@pytest.fixture()
def cluster_backend() -> ClusterBackend:
    """
    Return a cluster backend to use.
    """
    return DCOS_Docker(
        # We put this files in the `/tmp` directory because that is
        # writable on the Vagrant VM.
        workspace_path=Path('/tmp'),
        generate_config_path=Path('/tmp/dcos_generate_config.sh'),
        dcos_docker_path=Path('/tmp/dcos-docker'),
    )


@pytest.fixture()
def enterprise_cluster_backend() -> ClusterBackend:
    """
    Return a DC/OS Enterprise cluster backend to use.
    """
    return DCOS_Docker(
        # We put this files in the `/tmp` directory because that is
        # writable on the Vagrant VM.
        workspace_path=Path('/tmp'),
        generate_config_path=Path('/tmp/dcos_generate_config.ee.sh'),
        dcos_docker_path=Path('/tmp/dcos-docker'),
    )
