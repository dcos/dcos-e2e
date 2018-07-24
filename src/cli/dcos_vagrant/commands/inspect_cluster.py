"""
Tools for inspecting existing clusters.
"""

import json
from typing import Any, Dict  # noqa: F401

import click

from cli.common.options import existing_cluster_id_option
from cli.common.utils import check_cluster_id_exists

from ._common import ClusterVMs, VMInspectView, existing_cluster_ids


@click.command('inspect')
@existing_cluster_id_option
def inspect_cluster(cluster_id: str) -> None:
    """
    Show cluster details.
    """
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
        key: [VMInspectView(vm).to_dict() for vm in vms]
        for key, vms in keys.items()
    }

    data = {
        'Cluster ID': cluster_id,
        'Web UI': web_ui,
        'Nodes': nodes,
    }  # type: Dict[Any, Any]
    click.echo(
        json.dumps(data, indent=4, separators=(',', ': '), sort_keys=True),
    )
