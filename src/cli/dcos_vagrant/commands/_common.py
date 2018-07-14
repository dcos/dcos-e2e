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
