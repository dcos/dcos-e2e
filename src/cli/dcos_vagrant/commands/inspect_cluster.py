"""
Tools for inspecting existing clusters.
"""

import json
from typing import Any, Dict  # noqa: F401

import click

from ._common import ClusterVMs
from ._options import existing_cluster_id_option


@click.command('inspect')
@existing_cluster_id_option
def inspect_cluster(cluster_id: str, env: bool) -> None:
    """
    Show cluster details.
    """
    cluster_vms = ClusterVMs(cluster_id=cluster_id)
    master = next(iter(cluster_vms.cluster.masters))
    web_ui = 'http://' + str(master.private_ip_address)
    vagrant_client = cluster_vms.vagrant_client
    import pdb; pdb.set_trace()
    ssh_key = cluster_containers.workspace_dir / 'ssh' / 'id_rsa'

    keys = {
        'masters': cluster_containers.masters,
        'agents': cluster_containers.agents,
        'public_agents': cluster_containers.public_agents,
    }

    nodes = {
        key: [
            ContainerInspectView(container).to_dict()
            for container in containers
        ]
        for key, containers in keys.items()
    }

    data = {
        'Cluster ID': cluster_id,
        'Web UI': web_ui,
        'Nodes': nodes,
        'SSH key': str(ssh_key),
    }  # type: Dict[Any, Any]
    click.echo(
        json.dumps(data, indent=4, separators=(',', ': '), sort_keys=True),
    )
