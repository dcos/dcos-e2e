"""
Common code for minidcos docker CLI modules.
"""

import functools
import json
import os
from collections import defaultdict
from ipaddress import IPv4Address
from pathlib import Path
from shutil import rmtree
from typing import Dict  # noqa: F401
from typing import Any, Optional, Set

import yaml

from dcos_e2e.backends import Vagrant
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node
from dcos_e2e_cli._vendor import vertigo_py
from dcos_e2e_cli.common.base_classes import ClusterRepresentation

CLUSTER_ID_DESCRIPTION_KEY = 'dcos_e2e.cluster_id'
WORKSPACE_DIR_DESCRIPTION_KEY = 'dcos_e2e.workspace_dir'


@functools.lru_cache()
def _description_from_vm_name(vm_name: str) -> str:
    """
    Given the name of a VirtualBox VM, return its description.
    """
    virtualbox_vm = vertigo_py.VM(name=vm_name)  # type: ignore
    info = virtualbox_vm.parse_info()  # type: Dict[str, str]
    escaped_description = info.get('description', '')
    description = escaped_description.encode().decode('unicode_escape')
    return str(description)


def _state_from_vm_name(vm_name: str) -> str:
    """
    Given the name of a VirtualBox VM, return its VM state, such as
    "running".

    See
    https://www.virtualbox.org/sdkref/_virtual_box_8idl.html#a80b08f71210afe16038e904a656ed9eb
    for possible states.
    """
    virtualbox_vm = vertigo_py.VM(name=vm_name)  # type: ignore
    info = virtualbox_vm.parse_info()  # type: Dict[str, str]
    return info['VMState']


# We do not cache the results of this function.
# This is because the VM names may change during one command - a ``create``
# command.
def vm_names_by_cluster(running_only: bool = False) -> Dict[str, Set[str]]:
    """
    Return a mapping of Cluster IDs to the names of VMs in those clusters.

    Args:
        running_only: If ``True`` only return running VMs.
    """
    ls_output = bytes(vertigo_py.ls(option='vms'))  # type: ignore
    lines = ls_output.decode().strip().split('\n')
    lines = [line for line in lines if line]
    result = defaultdict(set)  # type: Dict[str, Set[str]]
    for line in lines:
        vm_name_in_quotes, _ = line.rsplit(' ', 1)
        vm_name = vm_name_in_quotes[1:-1]
        state = _state_from_vm_name(vm_name=vm_name)
        description = _description_from_vm_name(vm_name=vm_name)
        try:
            data = json.loads(s=description)
        except json.decoder.JSONDecodeError:
            continue
        if running_only and state != 'running':
            # We do not show e.g. aborted VMs when listing clusters.
            # For example, a VM is aborted when the host is rebooted.
            # This is problematic as we cannot assume that the workspace
            # directory,
            # which might be in /tmp/ is still there.
            #
            # We do not show paused VMs when listing clusters.
            # A VM can be manually paused.
            # This can be problematic if someone pauses a VM, then creates a
            # new one with the same cluster ID.
            # However, we work on the assumption that a user will not manually
            # interfere with VirtualBox.
            continue
        # A VM is in a cluster if it has a description and that description is
        # valid JSON and has a known key.
        cluster_id = data.get(CLUSTER_ID_DESCRIPTION_KEY)
        if cluster_id is None:
            continue
        result[cluster_id].add(vm_name)
    return result


@functools.lru_cache()
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

    results = yaml.load(property_result, Loader=yaml.FullLoader)
    if results == 'No value set!':
        return None
    return IPv4Address(results['Value'])


def existing_cluster_ids() -> Set[str]:
    """
    Return the IDs of existing clusters.
    """
    return set(vm_names_by_cluster(running_only=True).keys())


class ClusterVMs(ClusterRepresentation):
    """
    A representation of a cluster constructed from Vagrant VMs.
    """

    def __init__(self, cluster_id: str) -> None:
        """
        Args:
            cluster_id: The ID of the cluster.
        """
        self._cluster_id = cluster_id

    def to_node(self, node_representation: str) -> Node:
        """
        Return the ``Node`` that is represented by a given VM name.
        """
        vm_name = node_representation
        address = _ip_from_vm_name(vm_name=vm_name)
        assert isinstance(address, IPv4Address)
        client = self.vagrant_client()
        ssh_key_path = Path(client.keyfile(vm_name=vm_name))
        ssh_user = str(client.user(vm_name=vm_name))
        return Node(
            public_ip_address=address,
            private_ip_address=address,
            default_user=ssh_user,
            ssh_key_path=ssh_key_path,
        )

    def to_dict(self, node_representation: str) -> Dict[str, str]:
        """
        Return information to be shown to users which is unique to this node.
        """
        vm_name = node_representation
        ip_address = _ip_from_vm_name(vm_name=vm_name)

        if vm_name in self.masters:
            role = 'master'
            role_names = self.masters
        elif vm_name in self.agents:
            role = 'agent'
            role_names = self.agents
        elif vm_name in self.public_agents:
            role = 'public_agent'
            role_names = self.public_agents

        sorted_ips = sorted(
            [_ip_from_vm_name(vm_name=name) for name in role_names],
        )
        index = sorted_ips.index(ip_address)
        client = self.vagrant_client()
        ssh_user = str(client.user(vm_name=vm_name))
        ssh_key_path = Path(client.keyfile(vm_name=vm_name))

        return {
            'e2e_reference': '{role}_{index}'.format(role=role, index=index),
            'vm_name': vm_name,
            'ip_address': str(ip_address),
            'ssh_user': ssh_user,
            'ssh_key': str(ssh_key_path),
        }

    @functools.lru_cache()
    def _vm_names(self) -> Set[str]:
        """
        Return VirtualBox and Vagrant names of VMs in this cluster.
        """
        return vm_names_by_cluster(running_only=True)[self._cluster_id]

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
        # see https://jira.d2iq.com/browse/DCOS_OSS-3851.
        vm_names = self._vm_names()
        return set(name for name in vm_names if '-master-' in name)

    @property
    def agents(self) -> Set[str]:
        """
        VM names which represent agent nodes.
        """
        vm_names = self._vm_names()
        return set(
            name for name in vm_names
            if '-agent-' in name and '-public-agent-' not in name
        )

    @property
    def public_agents(self) -> Set[str]:
        """
        VM names which represent public agent nodes.
        """
        vm_names = self._vm_names()
        return set(name for name in vm_names if '-public-agent-' in name)

    @property
    def _workspace_dir(self) -> Path:
        """
        The workspace directory to put temporary files in.
        """
        vm_names = self._vm_names()
        one_vm_name = next(iter(vm_names))
        description = _description_from_vm_name(vm_name=one_vm_name)
        data = json.loads(s=description)
        workspace_dir = data[WORKSPACE_DIR_DESCRIPTION_KEY]
        return Path(workspace_dir)

    # Use type "Any" so we do not have to import ``vagrant`` because importing
    # that shows a warning on machines that do not have Vagrant installed.
    @functools.lru_cache()
    def vagrant_client(self) -> Any:
        """
        A Vagrant client attached to this cluster.
        """
        vm_names = self._vm_names()

        # We are not creating VMs so these have to be set but do not
        # matter as long as they are valid to use the Vagrantfile.
        backend = Vagrant()
        description = backend.virtualbox_description
        vm_memory_mb = backend.vm_memory_mb
        vagrant_box_version = backend.vagrant_box_version
        vagrant_box_url = backend.vagrant_box_url

        vagrant_env = {
            'HOME': os.environ['HOME'],
            'PATH': os.environ['PATH'],
            'VM_NAMES': ','.join(list(vm_names)),
            'VM_DESCRIPTION': description,
            'VM_MEMORY': str(vm_memory_mb),
            'VAGRANT_BOX_VERSION': vagrant_box_version,
            'VAGRANT_BOX_URL': vagrant_box_url,
        }

        [vagrant_root_parent] = [
            item for item in self._workspace_dir.iterdir()
            if item.is_dir() and item.name != 'genconf'
        ]

        # We ignore files such as .DS_Store files.
        [
            vagrant_root,
        ] = [item for item in vagrant_root_parent.iterdir() if item.is_dir()]

        # We import Vagrant here instead of at the top of the file because, if
        # the Vagrant executable is not found, a warning is logged.
        #
        # We want to avoid that warning for users of other backends who do not
        # have the Vagrant executable.
        import vagrant
        vagrant_client = vagrant.Vagrant(
            root=str(vagrant_root),
            env=vagrant_env,
            quiet_stdout=False,
            quiet_stderr=True,
        )

        return vagrant_client

    @property
    def base_config(self) -> Dict[str, Any]:
        """
        Return a base configuration for installing DC/OS OSS.
        """
        backend = Vagrant()

        return {
            **self.cluster.base_config,
            **backend.base_config,
        }

    def destroy(self) -> None:
        """
        Destroy this cluster.
        """
        workspace_dir = self._workspace_dir
        self.vagrant_client().destroy()
        rmtree(path=str(workspace_dir), ignore_errors=True)
