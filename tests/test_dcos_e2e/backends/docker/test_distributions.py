"""
Tests for the ``linux_distribution`` option on the Docker backend.
"""

import uuid
from pathlib import Path

# See https://github.com/PyCQA/pylint/issues/1536 for details on why the errors
# are disabled.
import pytest
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


class TestDefaults:
    """
    Tests for not using a custom Linux distribution.
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

    @pytest.mark.parametrize(
        'unsupported_linux_distribution',
        set(Distribution) - {Distribution.CENTOS_7, Distribution.COREOS}
    )
    def test_custom_choice(
        self,
        unsupported_linux_distribution: Distribution,
    ) -> None:
        """
        Starting a cluster with a non-default Linux distribution raises a
        `NotImplementedError`.
        """
        with pytest.raises(NotImplementedError):
            Docker(linux_distribution=unsupported_linux_distribution)


class TestCoreOS:
    """
    Tests for the CoreOS distribution option.
    """

    def test_coreos_oss(
        self,
        oss_artifact: Path,
    ) -> None:
        """
        DC/OS OSS can start up on CoreOS.
        """
        with Cluster(
            cluster_backend=Docker(linux_distribution=Distribution.COREOS),
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

        assert node_distribution == Distribution.COREOS

    def test_coreos_enterprise(
        self,
        enterprise_artifact: Path,
        license_key_contents: str,
    ) -> None:
        """
        DC/OS Enterprise can start up on CoreOS.
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
            cluster_backend=Docker(linux_distribution=Distribution.COREOS),
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

        assert node_distribution == Distribution.COREOS
