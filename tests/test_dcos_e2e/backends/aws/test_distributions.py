"""
Test DC/OS on all supported distributions on Amazon Web Services.
"""

import uuid

import pytest
from passlib.hash import sha512_crypt

from dcos_e2e.backends import AWS
from dcos_e2e.cluster import Cluster
from dcos_e2e.distributions import Distribution
from dcos_e2e.node import Node, Output


def _get_node_distribution(node: Node) -> Distribution:
    """
    Given a ``Node``, return the ``Distribution`` on that node.
    """
    cat_cmd = node.run(
        args=['cat /etc/*-release'],
        shell=True,
    )

    version_info = cat_cmd.stdout
    version_info_lines = [
        line for line in version_info.decode().split('\n') if '=' in line
    ]
    version_data = dict(item.split('=') for item in version_info_lines)

    distributions = {
        ('"centos"', '"7"'): Distribution.CENTOS_7,
        ('"rhel"', '"7.4"'): Distribution.RHEL_7,
        ('coreos', '1911.3.0'): Distribution.COREOS,
        ('coreos', '1632.3.0'): Distribution.COREOS,
        ('coreos', '1967.6.0'): Distribution.COREOS,
    }

    distro_id = version_data['ID'].strip()
    distro_version_id = version_data['VERSION_ID'].strip()

    return distributions[(distro_id, distro_version_id)]


def _oss_distribution_test(
    distribution: Distribution,
    oss_installer_url: str,
) -> None:
    """
    Assert that given a ``linux_distribution``, an open source DC/OS
    ``Cluster`` with the Linux distribution is started.

    We use this rather than pytest parameterization so that we can separate
    the tests in ``.travis.yml``.
    """
    cluster_backend = AWS(linux_distribution=distribution)
    with Cluster(
        cluster_backend=cluster_backend,
        masters=1,
        agents=0,
        public_agents=0,
    ) as cluster:
        cluster.install_dcos_from_url(
            dcos_installer=oss_installer_url,
            dcos_config=cluster.base_config,
            output=Output.CAPTURE,
            ip_detect_path=cluster_backend.ip_detect_path,
        )
        cluster.wait_for_dcos_oss()
        (master, ) = cluster.masters
        node_distribution = _get_node_distribution(node=master)

    assert node_distribution == distribution


def _enterprise_distribution_test(
    distribution: Distribution,
    ee_installer_url: str,
    license_key_contents: str,
) -> None:
    """
    Assert that given a ``linux_distribution``, a DC/OS Enterprise ``Cluster``
    with the Linux distribution is started.

    We use this rather than pytest parameterization so that we can separate
    the tests in ``.travis.yml``.
    """
    superuser_username = str(uuid.uuid4())
    superuser_password = str(uuid.uuid4())
    config = {
        'superuser_username': superuser_username,
        'superuser_password_hash': sha512_crypt.hash(superuser_password),
        'fault_domain_enabled': False,
        'license_key_contents': license_key_contents,
    }

    cluster_backend = AWS(linux_distribution=distribution)
    with Cluster(
        cluster_backend=cluster_backend,
        masters=1,
        agents=0,
        public_agents=0,
    ) as cluster:
        cluster.install_dcos_from_url(
            dcos_installer=ee_installer_url,
            dcos_config={
                **cluster.base_config,
                **config,
            },
            ip_detect_path=cluster_backend.ip_detect_path,
            output=Output.CAPTURE,
        )
        cluster.wait_for_dcos_ee(
            superuser_username=superuser_username,
            superuser_password=superuser_password,
        )
        (master, ) = cluster.masters
        node_distribution = _get_node_distribution(node=master)

    assert node_distribution == distribution


class TestCentos7:
    """
    Tests for using CentOS 7.
    """

    def test_default_distribution(self) -> None:
        """
        The default Linux distribution is CentOS 7.

        This test does not wait for DC/OS and we do not test DC/OS Enterprise
        because these are covered by other tests which use the default
        settings.
        """
        with Cluster(
            cluster_backend=AWS(),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            node_distribution = _get_node_distribution(node=master)

        assert node_distribution == Distribution.CENTOS_7

    def test_set_distribution(self) -> None:
        """
        The Linux distribution can be set to CentOS 7.

        This test does not wait for DC/OS and we do not test DC/OS Enterprise
        because these are covered by other tests which use the default
        settings.
        """

        with Cluster(
            # The distribution is also CentOS 7 if it is explicitly set.
            cluster_backend=AWS(linux_distribution=Distribution.CENTOS_7),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            node_distribution = _get_node_distribution(node=master)

        assert node_distribution == Distribution.CENTOS_7


@pytest.mark.xfail(reason='dcos_launch does not have working RHEL image')
class TestRHEL7:
    """
    Tests for the Red Hat Enterprise Linux 7 distribution option.
    """

    def test_oss(
        self,
        oss_installer_url: str,
    ) -> None:
        """
        DC/OS OSS can start up on RHEL7.
        """
        _oss_distribution_test(
            distribution=Distribution.RHEL_7,
            oss_installer_url=oss_installer_url,
        )

    def test_enterprise(
        self,
        ee_installer_url: str,
        license_key_contents: str,
    ) -> None:
        """
        DC/OS Enterprise can start up on RHEL7.
        """
        _enterprise_distribution_test(
            distribution=Distribution.RHEL_7,
            ee_installer_url=ee_installer_url,
            license_key_contents=license_key_contents,
        )
