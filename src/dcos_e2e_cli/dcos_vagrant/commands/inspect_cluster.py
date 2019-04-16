"""
Tools for inspecting existing clusters.
"""

import json
from typing import Any  # noqa: F401
from typing import Dict  # noqa: F401

import click

from dcos_e2e_cli.common.options import (
    existing_cluster_id_option,
    verbosity_option,
)
from dcos_e2e_cli.common.utils import check_cluster_id_exists, set_logging
from dcos_e2e_cli.common.variants import get_cluster_variant

from ._common import ClusterVMs, VMInspectView, existing_cluster_ids


@click.command('inspect')
@existing_cluster_id_option
@verbosity_option
def inspect_cluster(cluster_id: str, verbose: int) -> None:
    """
    Show cluster details.
    """
    set_logging(verbosity_level=verbose)
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    cluster_vms = ClusterVMs(cluster_id=cluster_id)
    keys = {
        'masters': cluster_vms.masters,
        'agents': cluster_vms.agents,
        'public_agents': cluster_vms.public_agents,
    }
    master = next(iter(cluster_vms.cluster.masters))
    web_ui = 'http://' + str(master.private_ip_address)
    nodes = {
        key: [
            VMInspectView(vm_name=vm, cluster_vms=cluster_vms).to_dict()
            for vm in vms
        ]
        for key, vms in keys.items()
    }

    cluster = cluster_vms.cluster
    dcos_variant = get_cluster_variant(cluster=cluster)
    variant_name = str(dcos_variant if dcos_variant else None)

    data = {
        'Cluster ID': cluster_id,
        'Web UI': web_ui,
        'Nodes': nodes,
        'SSH Default User': cluster_vms.ssh_default_user,
        'SSH key': str(cluster_vms.ssh_key_path),
        'DC/OS Variant': variant_name,
    }  # type: Dict[str, Any]
    click.echo(
        json.dumps(data, indent=4, separators=(',', ': '), sort_keys=True),
    )
