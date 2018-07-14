"""
Common code for dcos-docker CLI modules.
"""

import json
import os
from pathlib import Path
from shutil import rmtree
from typing import Dict  # noqa: F401
from typing import Set

from cli._vendor import vertigo_py

CLUSTER_ID_DESCRIPTION_KEY = 'dcos_e2e.cluster_id'
WORKSPACE_DIR_DESCRIPTION_KEY = 'dcos_e2e.workspace_dir'


def _description_from_vm_name(vm_name: str) -> str:
    """
    Given the name of a VirtualBox VM, return its description.
    """
    virtualbox_vm = vertigo_py.VM(name=vm_name)  # type: ignore
    info = virtualbox_vm.parse_info()  # type: Dict[str, str]
    escaped_description = info.get('description', '')
    description = escaped_description.encode().decode('unicode_escape')
    return str(description)


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

    def _to_node(self, vm_name: str) -> Node:
        """
        Return the ``Node`` that is represented by a given VM name.
        """
        address = IPv4Address(container.attrs['NetworkSettings']['IPAddress'])
        ssh_key_path = self.workspace_dir / 'ssh' / 'id_rsa'
        return Node(
            public_ip_address=address,
            private_ip_address=address,
            default_user='root',
            ssh_key_path=ssh_key_path,
            default_transport=self._transport,
        )

    @property
    def _vm_names(self) -> Set[str]:
        """
        XXX
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
                vm_names.append(vm_name)

    @property
    def is_enterprise(self) -> bool:
        """
        Return whether the cluster is a DC/OS Enterprise cluster.
        """
        vm_names = self._vm_names
        one_vm_name = next(iter(vm_names))
        description = _description_from_vm_name(vm_name=one_vm_name)
        data = json.loads(s=description)
        variant = data[VARIANT_DESCRIPTION_KEY]
        return bool(variant == 'ee')

    @property
    def cluster(self) -> Cluster:
        """
        Return a ``Cluster`` constructed from the Vms.
        """
        return Cluster.from_nodes(
            masters=set(map(self._to_node, masters)),
            agents=set(map(self._to_node, agents)),
            public_agents=set(map(self._to_node, public_agents)),
        )

    @property
    def workspace_dir(self) -> Path:
        vm_names = self._vm_names
        one_vm_name = next(iter(vm_names))
        description = _description_from_vm_name(vm_name=one_vm_name)
        data = json.loads(s=description)
        workspace_dir = data[WORKSPACE_DIR_DESCRIPTION_KEY]
        return Path(workspace_dir)

    def destroy(self) -> None:
        """
        Destroy this cluster.
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
        vagrant_client.destroy()
        rmtree(path=str(workspace_dir), ignore_errors=True)
