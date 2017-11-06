"""
Helpers for running tests with `pytest`.
"""

import pytest

from dcos_e2e.backends import ClusterBackend, Docker


@pytest.fixture(scope='session')
def cluster_backend() -> ClusterBackend:
    """
    Return a cluster backend to use.
    """
    return Docker()


@pytest.fixture(scope='session')
def oss_artifact() -> str:
    """
    Return the url to a local artifact for DC/OS OSS.
    """
    return 'file:///tmp/dcos_generate_config.sh'


@pytest.fixture(scope='session')
def enterprise_artifact() -> str:
    """
    Return the url to a local artifact for DC/OS Enterprise.
    """
    return 'file:///tmp/dcos_generate_config.ee.sh'


@pytest.fixture(scope='session')
def oss_artifact_url() -> str:
    """
    Return the url to a for DC/OS Enterprise artifact on a HTTPS server.
    """
    return 'https://downloads.dcos.io/dcos/stable/dcos_generate_config.sh'
