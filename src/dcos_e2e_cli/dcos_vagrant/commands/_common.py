"""
Common code for minidcos docker CLI modules.
"""

import json
import os
from ipaddress import IPv4Address
from pathlib import Path
from shutil import rmtree
from typing import Dict  # noqa: F401
from typing import Any, Optional, Set

import yaml

from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node
from dcos_e2e_cli._vendor import vertigo_py
from dcos_e2e_cli._vendor.dcos_installer_tools import DCOSVariant

CLUSTER_ID_DESCRIPTION_KEY = 'dcos_e2e.cluster_id'
WORKSPACE_DIR_DESCRIPTION_KEY = 'dcos_e2e.workspace_dir'
VARIANT_DESCRIPTION_KEY = 'dcos_e2e.variant'
VARIANT_ENTERPRISE_DESCRIPTION_VALUE = 'ee'
VARIANT_OSS_DESCRIPTION_VALUE = 'oss'


def _description_from_vm_name(vm_name: str) -> str:
    """
    Given the name of a VirtualBox VM, return its description.
    """
    virtualbox_vm = vertigo_py.VM(name=vm_name)  # type: ignore
    info = virtualbox_vm.parse_info()  # type: Dict[str, str]
    escaped_description = info.get('description', '')
    description = escaped_description.encode().decode('unicode_escape')
    return str(description)


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
    property_result = vertigo_py.execute(args=args)  # type: ignore
    results = yaml.load(property_result)
    if results == 'No value set!':
        return None
    return IPv4Address(results['Value'])


def existing_cluster_ids() -> Set[str]:
    """
    Return the IDs of existing clusters.
    """
    ls_output = vertigo_py.ls()  # type: ignore
    vm_ls_output = ls_output['vms']
    lines = vm_ls_output.decode().strip().split('\n')
    lines = [line for line in lines if line]
    cluster_ids = set()
    for line in lines:
        vm_name_in_quotes, _ = line.split(' ')
        vm_name = vm_name_in_quotes[1:-1]
        description = _description_from_vm_name(vm_name=vm_name)
        try:
            data = json.loads(s=description)
        except json.decoder.JSONDecodeError:
            continue

        cluster_id = data.get(CLUSTER_ID_DESCRIPTION_KEY)
        cluster_ids.add(cluster_id)

    return cluster_ids - set([None])


class VMInspectView:
    """
    Details of a node from a VM.
    """

    def __init__(self, vm_name: str) -> None:
        """
        Args:
            vm_name: The name of the VM which represents the node.
        """
        self._vm_name = vm_name

    def to_dict(self) -> Dict[str, str]:
        """
        Return dictionary with information to be shown to users.
        """
        ip_address = _ip_from_vm_name(vm_name=self._vm_name)
        description = _description_from_vm_name(vm_name=self._vm_name)
        data = json.loads(s=description)
        cluster_id = data[CLUSTER_ID_DESCRIPTION_KEY]
        cluster_vms = ClusterVMs(cluster_id=cluster_id)
        vagrant_client = cluster_vms.vagrant_client

        if self._vm_name in cluster_vms.masters:
            role = 'master'
            role_names = cluster_vms.masters
        elif self._vm_name in cluster_vms.agents:
            role = 'agent'
            role_names = cluster_vms.agents
        elif self._vm_name in cluster_vms.public_agents:
            role = 'public_agent'
            role_names = cluster_vms.public_agents

        sorted_ips = sorted(
            [_ip_from_vm_name(vm_name=name) for name in role_names],
        )
        index = sorted_ips.index(ip_address)

        return {
            'e2e_reference': '{role}_{index}'.format(role=role, index=index),
            'vm_name': self._vm_name,
            'ip_address': str(ip_address),
            'ssh_key': vagrant_client.keyfile(vm_name=self._vm_name),
            'ssh_user': vagrant_client.user(vm_name=self._vm_name),
            'vagrant_root': vagrant_client.root,
        }


class ClusterVMs:
    """
    A representation of a cluster constructed from Vagrant VMs.
    """

    def __init__(self, cluster_id: str) -> None:
        """
        Args:
            cluster_id: The ID of the cluster.
        """
        self._cluster_id = cluster_id

    def to_node(self, vm_name: str) -> Node:
        """
        Return the ``Node`` that is represented by a given VM name.
        """
        client = self.vagrant_client
        address = _ip_from_vm_name(vm_name=vm_name)
        assert isinstance(address, IPv4Address)
        ssh_key_path = Path(client.keyfile(vm_name=vm_name))
        default_user = client.user(vm_name=vm_name)
        return Node(
            public_ip_address=address,
            private_ip_address=address,
            default_user=default_user,
            ssh_key_path=ssh_key_path,
        )

    @property
    def _vm_names(self) -> Set[str]:
        """
        Return VirtualBox and Vagrant names of VMs in this cluster.
        """
        ls_output = vertigo_py.ls()  # type: ignore
        vm_ls_output = ls_output['vms']
        lines = vm_ls_output.decode().strip().split('\n')
        lines = [line for line in lines if line]
        vm_names = set()
        for line in lines:
            vm_name_in_quotes, _ = line.split(' ')
            vm_name = vm_name_in_quotes[1:-1]
            description = _description_from_vm_name(vm_name=vm_name)
            try:
                data = json.loads(s=description)
            except json.decoder.JSONDecodeError:
                continue

            cluster_id = data.get(CLUSTER_ID_DESCRIPTION_KEY)
            if cluster_id == self._cluster_id:
                vm_names.add(vm_name)

        return vm_names

    @property
    def dcos_variant(self) -> DCOSVariant:
        """
        Return the DC/OS variant of the cluster.
        """
        vm_names = self._vm_names
        one_vm_name = next(iter(vm_names))
        description = _description_from_vm_name(vm_name=one_vm_name)
        data = json.loads(s=description)
        vm_variant_value = data[VARIANT_DESCRIPTION_KEY]
        return {
            VARIANT_ENTERPRISE_DESCRIPTION_VALUE: DCOSVariant.ENTERPRISE,
            VARIANT_OSS_DESCRIPTION_VALUE: DCOSVariant.OSS,
        }[vm_variant_value]

    @property
    def cluster(self) -> Cluster:
        """
        Return a ``Cluster`` constructed from the VMs.
        """
        return Cluster.from_nodes(
            masters=set(map(self.to_node, self.masters)),
            agents=set(map(self.to_node, self.agents)),
            public_agents=set(map(self.to_node, self.public_agents)),
        )

    @property
    def masters(self) -> Set[str]:
        """
        VM names which represent master nodes.
        """
        # This is a hack as it depends on an internal implementation detail of
        # the library.
        # Instead, we should set different Virtualbox descriptions for
        # different node types.
        # see https://jira.mesosphere.com/browse/DCOS_OSS-3851.
        return set(name for name in self._vm_names if '-master-' in name)

    @property
    def agents(self) -> Set[str]:
        """
        VM names which represent agent nodes.
        """
        return set(
            name for name in self._vm_names
            if '-agent-' in name and '-public-agent-' not in name
        )

    @property
    def public_agents(self) -> Set[str]:
        """
        VM names which represent public agent nodes.
        """
        return set(name for name in self._vm_names if '-public-agent-' in name)

    @property
    def workspace_dir(self) -> Path:
        """
        The workspace directory to put temporary files in.
        """
        vm_names = self._vm_names
        one_vm_name = next(iter(vm_names))
        description = _description_from_vm_name(vm_name=one_vm_name)
        data = json.loads(s=description)
        workspace_dir = data[WORKSPACE_DIR_DESCRIPTION_KEY]
        return Path(workspace_dir)

    # Use type "Any" so we do not have to import ``vagrant`` because importing
    # that shows a warning on machines that do not have Vagrant installed.
    @property
    def vagrant_client(self) -> Any:
        """
        A Vagrant client attached to this cluster.
        """
        vm_names = self._vm_names
        one_vm_name = next(iter(vm_names))
        description = _description_from_vm_name(vm_name=one_vm_name)

        vagrant_env = {
            'PATH': os.environ['PATH'],
            'VM_NAMES': ','.join(list(vm_names)),
            'VM_DESCRIPTION': description,
        }

        # We import Vagrant here instead of at the top of the file because, if
        # the Vagrant executable is not found, a warning is logged.
        #
        # We want to avoid that warning for users of other backends who do not
        # have the Vagrant executable.
        import vagrant

        [vagrant_root_parent] = [
            item for item in self.workspace_dir.iterdir()
            if item.is_dir() and item.name != 'genconf'
        ]

        [vagrant_root] = list(vagrant_root_parent.iterdir())

        vagrant_client = vagrant.Vagrant(
            root=str(vagrant_root),
            env=vagrant_env,
            quiet_stdout=False,
            quiet_stderr=True,
        )

        return vagrant_client

    def destroy(self) -> None:
        """
        Destroy this cluster.
        """
        workspace_dir = self.workspace_dir
        self.vagrant_client.destroy()
        rmtree(path=str(workspace_dir), ignore_errors=True)
