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
        dcos_docker_path=Path('/tmp/dcos-docker'),
    )


@pytest.fixture()
def oss_artifact() -> Path:
    """
    Return the path to an artifact for DC/OS OSS.
    """
    return Path('/tmp/dcos_generate_config.sh')


@pytest.fixture()
def enterprise_artifact() -> Path:
    """
    Return the path to an artifact for DC/OS Enterprise.
    """
    return Path('/tmp/dcos_generate_config.ee.sh')


@pytest.fixture()
def workspace_path() -> Path:
    """
    Return a directory in which we can put large temporary files.

    This uses `/tmp` because it is writable on the Vagrant VM.
    """
    return Path('/tmp')
