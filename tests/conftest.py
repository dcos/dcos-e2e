"""
Helpers for running tests with `pytest`.
"""

from pathlib import Path

import pytest

from dcos_e2e.backends import ClusterBackend, Docker


@pytest.fixture(scope='session')
def cluster_backend() -> ClusterBackend:
    """
    Return a cluster backend to use.
    """
    return Docker()


@pytest.fixture(scope='session')
def oss_artifact() -> Path:
    """
    Return the path to an artifact for DC/OS OSS.
    """
    return Path('/tmp/dcos_generate_config.sh')


@pytest.fixture(scope='session')
def enterprise_artifact() -> Path:
    """
    Return the path to an artifact for DC/OS Enterprise.
    """
    return Path('/tmp/dcos_generate_config.ee.sh')
