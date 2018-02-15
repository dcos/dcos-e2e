"""Tests for dcos_test_utils.helpers."""
from dcos_test_utils import helpers


def test_marathon_app_id_to_mesos_dns_subdomain():
    assert helpers.marathon_app_id_to_mesos_dns_subdomain('/app-1') == 'app-1'
    assert helpers.marathon_app_id_to_mesos_dns_subdomain('app-1') == 'app-1'
    assert helpers.marathon_app_id_to_mesos_dns_subdomain('/group-1/app-1') == 'app-1-group-1'
