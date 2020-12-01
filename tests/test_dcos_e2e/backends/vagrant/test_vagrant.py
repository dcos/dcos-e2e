"""
Tests for the Vagrant backend.
"""

import os
import uuid
from ipaddress import IPv4Address
from pathlib import Path
from typing import Optional

import pytest
import yaml

from dcos_e2e._vendor import vertigo_py
from dcos_e2e.backends import Vagrant
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node, Output


@pytest.mark.skipif(
    os.environ.get('TRAVIS') == 'true',
    reason='It is not possible to run VirtualBox on Travis CI',
)
@pytest.mark.skipif(
    os.environ.get('GITHUB_ACTIONS') == 'true',
    reason='It is not possible to run VirtualBox on GitHub Actions',
)
class TestRunIntegrationTest:  # pragma: no cover
    """
    Tests for functionality specific to the Vagrant backend.
    """

    def test_run_integration_test(
        self,
        oss_installer: Path,
    ) -> None:
        """
        It is possible to run DC/OS integration tests on Vagrant.
        This test module only requires a single master node.
        """
        cluster_backend = Vagrant()
        with Cluster(
            cluster_backend=cluster_backend,
            masters=1,
            agents=1,
            public_agents=1,
        ) as cluster:
            cluster.install_dcos_from_path(
                dcos_installer=oss_installer,
                dcos_config=cluster.base_config,
                output=Output.CAPTURE,
                ip_detect_path=cluster_backend.ip_detect_path,
            )

            cluster.wait_for_dcos_oss()

            # No error is raised with a successful command.
            cluster.run_with_test_environment(
                args=['pytest', '-vvv', '-s', '-x', 'test_units.py'],
                output=Output.CAPTURE,
            )


def _ip_from_vm_name(vm_name: str,
                     ) -> Optional[IPv4Address]:  # pragma: no cover
    """
    Given the name of a VirtualBox VM, return its IP address.
    """
    property_name = '/VirtualBox/GuestInfo/Net/1/V4/IP'
    args = [
        vertigo_py.constants.cmd,
        'guestproperty',
        'get',
        vm_name,
        property_name,
    ]
    property_result = vertigo_py.execute(args=args)  # type: ignore
    results = yaml.load(property_result, Loader=yaml.FullLoader)
    if results == 'No value set!':
        return None
    return IPv4Address(results['Value'])


def _description_from_vm_name(vm_name: str,
                              ) -> Optional[str]:  # pragma: no cover
    """
    Given the name of a VirtualBox VM, return its description address.
    """
    vertigo_vm = vertigo_py.VM(name=vm_name)  # type: ignore
    info = vertigo_vm.parse_info()
    if 'description' in info:
        return str(info['description'])
    return None


def _get_vm_from_node(node: Node) -> str:  # pragma: no cover
    """
    Return the container which represents the given ``node``.
    """
    ls_result = bytes(vertigo_py.ls(option='vms'))  # type: ignore
    lines = ls_result.decode().strip().split('\n')
    vm_names = set(line.split(' ')[0][1:-1] for line in lines)
    [node_vm] = [
        vm_name for vm_name in vm_names
        if _ip_from_vm_name(vm_name=vm_name) == node.private_ip_address
    ]
    return str(node_vm)


@pytest.mark.skipif(
    os.environ.get('TRAVIS') == 'true',
    reason='It is not possible to run VirtualBox on Travis CI',
)
@pytest.mark.skipif(
    os.environ.get('GITHUB_ACTIONS') == 'true',
    reason='It is not possible to run VirtualBox on GitHub Actions',
)
class TestVMDescription:  # pragma: no cover
    """
    Tests for the VirtualBox description of VMs representing nodes.
    """

    def test_default(self) -> None:
        """
        By default, VMs include an empty description.
        """
        with Cluster(
            cluster_backend=Vagrant(),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            new_vm_name = _get_vm_from_node(node=master)
            description = _description_from_vm_name(vm_name=new_vm_name)
            assert description is None

    def test_custom(self) -> None:
        """
        It is possible to set a custom description for VMs.
        """
        description = uuid.uuid4().hex
        with Cluster(
            cluster_backend=Vagrant(virtualbox_description=description),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            new_vm_name = _get_vm_from_node(node=master)
            vm_description = _description_from_vm_name(vm_name=new_vm_name)
            assert vm_description == description
