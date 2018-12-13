import os

import pytest

from dcos_test_utils import dcos_api, enterprise, logger

logger.setup(os.getenv('LOG_LEVEL', 'DEBUG'))


@pytest.fixture(scope='session')
def dcos_api_session_factory():
    is_enterprise = os.getenv('DCOS_ENTERPRISE', 'false').lower() == 'true'

    if is_enterprise:
        return enterprise.EnterpriseApiSession
    else:
        return dcos_api.DcosApiSession


@pytest.fixture(scope='session')
def dcos_api_session(dcos_api_session_factory):
    api = dcos_api_session_factory.create()
    api.wait_for_dcos()
    return api
