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
def inspect_cluster(cluster_id: str) -> None:
    """
    Show cluster details.
    """
    cluster_vms = ClusterVMs(cluster_id=cluster_id)
    master = next(iter(cluster_vms.cluster.masters))
    web_ui = 'http://' + str(master.private_ip_address)
    vagrant_client = cluster_vms.vagrant_client

    data = {
        'Cluster ID': cluster_id,
        'Web UI': web_ui,
        'Vagrant root': vagrant_client.root,
        'SSH key': vagrant_client.keyfile(),
        'SSH user': vagrant_client.user(),
    }  # type: Dict[Any, Any]
    click.echo(
        json.dumps(data, indent=4, separators=(',', ': '), sort_keys=True),
    )
