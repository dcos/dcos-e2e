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
    Return the path to a build artifact for DC/OS OSS master.
    """
    return Path('/tmp/dcos_generate_config.sh')


@pytest.fixture(scope='session')
def enterprise_artifact() -> Path:
    """
    Return the path to a build artifact for DC/OS Enterprise master.
    """
    return Path('/tmp/dcos_generate_config.ee.sh')


@pytest.fixture(scope='session')
def oss_1_10_artifact() -> Path:
    """
    Return the path to a build artifact for DC/OS OSS 1.10.
    """
    return Path('/tmp/dcos_generate_config_1_10.sh')


@pytest.fixture(scope='session')
def enterprise_1_10_artifact() -> Path:
    """
    Return the path to a build artifact for DC/OS Enterprise 1.10.
    """
    return Path('/tmp/dcos_generate_config_1_10.ee.sh')


@pytest.fixture(scope='session')
def oss_1_11_artifact() -> Path:
    """
    Return the path to a build artifact for DC/OS OSS 1.11.
    """
    return Path('/tmp/dcos_generate_config_1_11.sh')


@pytest.fixture(scope='session')
def enterprise_1_11_artifact() -> Path:
    """
    Return the path to a build artifact for DC/OS Enterprise 1.11.
    """
    return Path('/tmp/dcos_generate_config_1_11.ee.sh')


@pytest.fixture(scope='session')
def oss_artifact_url() -> str:
    """
    Return the url to a build artifact for DC/OS OSS.
    """
    return 'https://downloads.dcos.io/dcos/stable/dcos_generate_config.sh'


@pytest.fixture(scope='session')
def license_key_contents() -> str:
    """
    Return a license key suitable for use with the latest version of DC/OS.
    """
    return Path('/tmp/license-key.txt').read_text()
