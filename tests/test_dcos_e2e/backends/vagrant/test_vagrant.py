"""
Tests for the Vagrant backend.
"""

import uuid
from ipaddress import IPv4Address
from pathlib import Path
from typing import Optional

import yaml

from dcos_e2e._vendor import vertigo_py
from dcos_e2e.backends import Vagrant
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node


# We skip these tests because VirtualBox is not available on Travis CI.
class TestRunIntegrationTest:  # pragma: nocover
    """
    Tests for functionality specific to the Vagrant backend.
    """

    def test_run_integration_test(
        self,
        oss_artifact: Path,
    ) -> None:
        """
        It is possible to run DC/OS integration tests on Vagrant.
        This test module only requires a single master node.
        """
        with Cluster(
            cluster_backend=Vagrant(),
            masters=1,
            agents=1,
            public_agents=1,
        ) as cluster:
            cluster.install_dcos_from_path(
                build_artifact=oss_artifact,
                dcos_config=cluster.base_config,
                log_output_live=True,
            )

            cluster.wait_for_dcos_oss()

            # No error is raised with a successful command.
            cluster.run_integration_tests(
                pytest_command=['pytest', '-vvv', '-s', '-x', 'test_units.py'],
                log_output_live=True,
            )


def _ip_from_vm_name(vm_name: str) -> Optional[IPv4Address]:
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
    property_result = vertigo_py.execute(args=args)
    results = yaml.load(property_result)
    if results == 'No value set!':
        return
    return IPv4Address(results['Value'])


def _description_from_vm_name(vm_name: str) -> Optional[str]:
    """
    Given the name of a VirtualBox VM, return its description address.
    """
    vm = vertigo_py.VM(name=vm_name)
    info = vm.parse_info()
    return info.get('description')


def _get_vm_from_node(node: Node) -> str:
    """
    Return the container which represents the given ``node``.
    """
    lines = vertigo_py.ls(option='vms').decode().strip().split('\n')
    vm_names = set(line.split(' ')[0][1:-1] for line in lines)
    [node_vm] = [
        vm_name for vm_name in vm_names
        if _ip_from_vm_name(vm_name=vm_name) == node.private_ip_address
    ]
    return node_vm


# We skip these tests because VirtualBox is not available on Travis CI.
class TestVMDescription:  # pragma: nocover
    """
    Tests for the VirtualBox description of VMs representing nodes.
    """

    def test_default(self):
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

    def test_custom(self):
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
