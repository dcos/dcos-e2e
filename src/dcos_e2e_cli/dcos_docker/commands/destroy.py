"""
Tools for destroying clusters.
"""

import sys
from typing import List

import click
from halo import Halo

from dcos_e2e.node import Transport
from dcos_e2e_cli.common.options import existing_cluster_id_option
from dcos_e2e_cli.common.utils import check_cluster_id_exists

from ._common import ClusterContainers, existing_cluster_ids
from ._options import node_transport_option


@Halo(enabled=sys.stdout.isatty())
def _destroy_cluster(cluster_id: str, transport: Transport) -> None:
    """
    Destroy a cluster.

    Args:
        cluster_id: The ID of the cluster.
        transport: The transport to use for any communication with the cluster.
    """
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        transport=transport,
    )
    cluster_containers.destroy()


@click.command('destroy-list')
@click.argument('cluster_ids', nargs=-1, type=str)
@node_transport_option
def destroy_list(cluster_ids: List[str], transport: Transport) -> None:
    """
    Destroy clusters.

    To destroy all clusters, run
    ``minidcos docker destroy $(minidcos docker list)``.
    """
    for cluster_id in cluster_ids:
        if cluster_id not in existing_cluster_ids():
            warning = 'Cluster "{cluster_id}" does not exist'.format(
                cluster_id=cluster_id,
            )
            click.echo(warning, err=True)
            continue

        _destroy_cluster(cluster_id=cluster_id, transport=transport)
        click.echo(cluster_id)


@click.command('destroy')
@existing_cluster_id_option
@node_transport_option
def destroy(cluster_id: str, transport: Transport) -> None:
    """
    Destroy a cluster.
    """
    _destroy_cluster(cluster_id=cluster_id, transport=transport)
    click.echo(cluster_id)
