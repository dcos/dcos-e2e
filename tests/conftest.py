"""
Helpers for running tests with `pytest`.
"""
import os
from pathlib import Path
from urllib import request

import pytest

from dcos_e2e.backends import AWS, ClusterBackend, Docker


@pytest.fixture(scope='session')
def cluster_backend() -> ClusterBackend:
    """
    Return a cluster backend to use.
    """
    return Docker()


@pytest.fixture(scope='session')
def aws_backend() -> ClusterBackend:
    """
    Return a cluster backend to use.
    """
    tmp_dir_path = Path(os.environ['DCOS_E2E_TMP_DIR_PATH'])
    assert tmp_dir_path.exists() and tmp_dir_path.is_dir()

    test_public_ip = request.urlopen('https://api.ipify.org'
                                     ).read().decode('utf8')

    return AWS(
        aws_region=os.environ['DEFAULT_AWS_REGION'],
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        admin_location=test_public_ip + '/32',
        instance_type='m4.large',
        workspace_dir=tmp_dir_path,
    )


@pytest.fixture(scope='session')
def oss_artifact_url() -> str:
    """
    Return the path to an artifact for DC/OS OSS.
    """
    return 'https://downloads.dcos.io/dcos/stable/dcos_generate_config.sh'


@pytest.fixture(scope='session')
def oss_artifact() -> Path:
    """
    Return the path to a build artifact for DC/OS OSS.
    """
    return Path('/tmp/dcos_generate_config.sh')


@pytest.fixture(scope='session')
def enterprise_artifact() -> Path:
    """
    Return the path to a build artifact for DC/OS Enterprise.
    """
    return Path('/tmp/dcos_generate_config.ee.sh')
