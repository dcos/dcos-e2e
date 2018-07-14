"""
Common code for dcos-docker CLI modules.
"""

import json
from typing import Dict  # noqa: F401
from typing import Set

from cli._vendor import vertigo_py

CLUSTER_ID_DESCRIPTION_KEY = 'dcos_e2e.cluster_id'


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

    def destroy(self) -> None:
        """
        Destroy this cluster.
        """
        vagrant_env = {
            'PATH': os.environ['PATH'],
            'VM_NAMES': vm_names,
            'VM_DESCRIPTION': '',
        }

        # We import Vagrant here instead of at the top of the file because, if
        # the Vagrant executable is not found, a warning is logged.
        #
        # We want to avoid that warning for users of other backends who do not
        # have the Vagrant executable.
        import vagrant
        self._vagrant_client = vagrant.Vagrant(
            root=str(path),
            env=vagrant_env,
            quiet_stdout=False,
            quiet_stderr=True,
        )
        rmtree(path=str(self.workspace_dir), ignore_errors=True)
