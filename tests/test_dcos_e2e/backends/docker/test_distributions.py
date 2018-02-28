"""
Tests for the ``linux_distribution`` option on the Docker backend.
"""

import uuid
from pathlib import Path

from passlib.hash import sha512_crypt

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.distributions import Distribution
from dcos_e2e.node import Node


def _get_node_distribution(node: Node) -> Distribution:
    """
    Given a `Node`, return the `Distribution` on that node.
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
        ('ubuntu', '"16.04"'): Distribution.UBUNTU_16_04,
        ('coreos', '1298.7.0'): Distribution.COREOS,
        ('fedora', '23'): Distribution.FEDORA_23,
        ('debian', '"8"'): Distribution.DEBIAN_8,
    }

    distro_id = version_data['ID'].strip()
    distro_version_id = version_data['VERSION_ID'].strip()

    return distributions[(distro_id, distro_version_id)]


def _oss_distribution_test(
    distribution: Distribution,
    oss_artifact: Path,
) -> None:
    """
    Assert that given a ``linux_distribution``, an open source DC/OS
    ``Cluster`` with the Linux distribution is started.

    We use this rather than pytest parametrization so that we can separate
    the tests in ``.travis.yml``.
    """
    with Cluster(
        cluster_backend=Docker(linux_distribution=distribution),
        masters=1,
        agents=0,
        public_agents=0,
    ) as cluster:
        cluster.install_dcos_from_path(
            build_artifact=oss_artifact,
            log_output_live=True,
        )
        cluster.wait_for_dcos_oss()
        (master, ) = cluster.masters
        node_distribution = _get_node_distribution(node=master)

    assert node_distribution == distribution


def _enterprise_distribution_test(
    distribution: Distribution,
    enterprise_artifact: Path,
    license_key_contents: str,
) -> None:
    """
    Assert that given a ``linux_distribution``, a DC/OS Enterprise ``Cluster``
    with the Linux distribution is started.

    We use this rather than pytest parametrization so that we can separate
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

    with Cluster(
        cluster_backend=Docker(linux_distribution=distribution),
        masters=1,
        agents=0,
        public_agents=0,
    ) as cluster:
        cluster.install_dcos_from_path(
            build_artifact=enterprise_artifact,
            extra_config=config,
            log_output_live=True,
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

    def test_default(self) -> None:
        """
        The default Linux distribution is CentOS 7.

        This test does not wait for DC/OS and we do not test DC/OS Enterprise
        because these are covered by other tests which use the default
        settings.
        """
        with Cluster(
            cluster_backend=Docker(),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            node_distribution = _get_node_distribution(node=master)

        assert node_distribution == Distribution.CENTOS_7

        with Cluster(
            # The distribution is also CentOS 7 if it is explicitly set.
            cluster_backend=Docker(linux_distribution=Distribution.CENTOS_7),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            node_distribution = _get_node_distribution(node=master)

        assert node_distribution == Distribution.CENTOS_7


class TestCoreOS:
    """
    Tests for the CoreOS distribution option.
    """

    def test_oss(
        self,
        oss_artifact: Path,
    ) -> None:
        """
        DC/OS OSS can start up on CoreOS.
        """
        _oss_distribution_test(
            distribution=Distribution.COREOS,
            oss_artifact=oss_artifact,
        )

    def test_enterprise(
        self,
        enterprise_artifact: Path,
        license_key_contents: str,
    ) -> None:
        """
        DC/OS Enterprise can start up on CoreOS.
        """
        _enterprise_distribution_test(
            distribution=Distribution.COREOS,
            enterprise_artifact=enterprise_artifact,
            license_key_contents=license_key_contents,
        )


class TestUbuntu1604:
    """
    Tests for the Ubuntu 16.04 distribution option.
    """

    def test_oss(
        self,
        oss_artifact: Path,
    ) -> None:
        """
        DC/OS OSS can start up on Ubuntu 16.04.
        """
        _oss_distribution_test(
            distribution=Distribution.UBUNTU_16_04,
            oss_artifact=oss_artifact,
        )

    def test_enterprise(
        self,
        enterprise_artifact: Path,
        license_key_contents: str,
    ) -> None:
        """
        DC/OS Enterprise can start up on Ubuntu 16.04.
        """
        _enterprise_distribution_test(
            distribution=Distribution.UBUNTU_16_04,
            enterprise_artifact=enterprise_artifact,
            license_key_contents=license_key_contents,
        )


class TestFedora23:
    """
    Tests for the Fedora 23 distribution option.
    """

    def test_oss(
        self,
        oss_artifact: Path,
    ) -> None:
        """
        DC/OS OSS can start up on Fedora 23.
        """
        _oss_distribution_test(
            distribution=Distribution.FEDORA_23,
            oss_artifact=oss_artifact,
        )

    def test_enterprise(
        self,
        enterprise_artifact: Path,
        license_key_contents: str,
    ) -> None:
        """
        DC/OS Enterprise can start up on Fedora 23.
        """
        _enterprise_distribution_test(
            distribution=Distribution.FEDORA_23,
            enterprise_artifact=enterprise_artifact,
            license_key_contents=license_key_contents,
        )


class TestDebian8:
    """
    Tests for the Debian 8 distribution option.
    """

    def test_oss(
        self,
        oss_artifact: Path,
    ) -> None:
        """
        DC/OS OSS can start up on Debian 8.
        """
        _oss_distribution_test(
            distribution=Distribution.DEBIAN_8,
            oss_artifact=oss_artifact,
        )

    def test_enterprise(
        self,
        enterprise_artifact: Path,
        license_key_contents: str,
    ) -> None:
        """
        DC/OS Enterprise can start up on Debian 8.
        """
        _enterprise_distribution_test(
            distribution=Distribution.DEBIAN_8,
            enterprise_artifact=enterprise_artifact,
            license_key_contents=license_key_contents,
        )
