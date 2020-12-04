"""
Helpers for running tests with `pytest`.
"""
import os
from pathlib import Path

import pytest

from dcos_e2e.backends import Docker
from dcos_e2e.base_classes import ClusterBackend


@pytest.fixture(scope='session')
def cluster_backend() -> ClusterBackend:
    """
    Return a cluster backend to use.
    """
    return Docker()


@pytest.fixture(scope='session')
def oss_installer() -> Path:
    """
    Return the path to an installer for DC/OS OSS master.
    """
    return Path('/tmp/dcos_generate_config.sh')


@pytest.fixture(scope='session')
def enterprise_installer() -> Path:
    """
    Return the path to an installer for DC/OS Enterprise master.
    """
    return Path('/tmp/dcos_generate_config.ee.sh')


@pytest.fixture(scope='session')
def oss_1_9_installer() -> Path:
    """
    Return the path to an installer for DC/OS OSS 1.9.
    """
    return Path('/tmp/dcos_generate_config_1_9.sh')


@pytest.fixture(scope='session')
def enterprise_1_9_installer() -> Path:
    """
    Return the path to an installer for DC/OS Enterprise 1.9.
    """
    return Path('/tmp/dcos_generate_config_1_9.ee.sh')


@pytest.fixture(scope='session')
def oss_1_10_installer() -> Path:
    """
    Return the path to an installer for DC/OS OSS 1.10.
    """
    return Path('/tmp/dcos_generate_config_1_10.sh')


@pytest.fixture(scope='session')
def enterprise_1_10_installer() -> Path:
    """
    Return the path to an installer for DC/OS Enterprise 1.10.
    """
    return Path('/tmp/dcos_generate_config_1_10.ee.sh')


@pytest.fixture(scope='session')
def oss_1_11_installer() -> Path:
    """
    Return the path to an installer for DC/OS OSS 1.11.
    """
    return Path('/tmp/dcos_generate_config_1_11.sh')


@pytest.fixture(scope='session')
def enterprise_1_11_installer() -> Path:
    """
    Return the path to an installer for DC/OS Enterprise 1.11.
    """
    return Path('/tmp/dcos_generate_config_1_11.ee.sh')


@pytest.fixture(scope='session')
def oss_1_12_installer() -> Path:
    """
    Return the path to an installer for DC/OS OSS 1.12.
    """
    return Path('/tmp/dcos_generate_config_1_12.sh')


@pytest.fixture(scope='session')
def enterprise_1_12_installer() -> Path:
    """
    Return the path to an installer for DC/OS Enterprise 1.12.
    """
    return Path('/tmp/dcos_generate_config_1_12.ee.sh')


@pytest.fixture(scope='session')
def oss_1_13_installer() -> Path:
    """
    Return the path to an installer for DC/OS OSS 1.13.
    """
    return Path('/tmp/dcos_generate_config_1_13.sh')


@pytest.fixture(scope='session')
def enterprise_1_13_installer() -> Path:
    """
    Return the path to an installer for DC/OS Enterprise 1.13.
    """
    return Path('/tmp/dcos_generate_config_1_13.ee.sh')


@pytest.fixture(scope='session')
def oss_2_0_installer() -> Path:
    """
    Return the path to an installer for DC/OS OSS 2.0.
    """
    return Path('/tmp/dcos_generate_config_2_0.sh')


@pytest.fixture(scope='session')
def enterprise_2_0_installer() -> Path:
    """
    Return the path to an installer for DC/OS Enterprise 2.0.
    """
    return Path('/tmp/dcos_generate_config_2_0.ee.sh')


@pytest.fixture(scope='session')
def oss_2_1_installer() -> Path:
    """
    Return the path to an installer for DC/OS OSS 2.1.
    """
    return Path('/tmp/dcos_generate_config_2_1.sh')


@pytest.fixture(scope='session')
def enterprise_2_1_installer() -> Path:
    """
    Return the path to an installer for DC/OS Enterprise 2.1.
    """
    return Path('/tmp/dcos_generate_config_2_1.ee.sh')


@pytest.fixture(scope='session')
def oss_installer_url() -> str:
    """
    Return the url to an installer for DC/OS OSS.
    """
    return 'https://downloads.dcos.io/dcos/stable/dcos_generate_config.sh'


@pytest.fixture(scope='session')
def oss_2_1_installer_url() -> str:
    """
    Return the url to an installer for DC/OS OSS 2.1.
    """
    return (
        'https://downloads.dcos.io/dcos/stable/2.1.2/dcos_generate_config.sh'
    )


@pytest.fixture(scope='session')
def ee_installer_url() -> str:
    """
    Return the url to an installer for Enterprise DC/OS.
    """
    return os.environ['EE_MASTER_INSTALLER_URL']


@pytest.fixture(scope='session')
def license_key_contents() -> str:
    """
    Return a license key suitable for use with the latest version of DC/OS.
    """
    return Path('/tmp/license-key.txt').read_text()
