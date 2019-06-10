"""
Tools for destroying clusters.
"""

from typing import List

import click
from halo import Halo

from dcos_e2e.node import Transport
from dcos_e2e_cli.common.options import (
    enable_spinner_option,
    existing_cluster_id_option,
)
from dcos_e2e_cli.common.utils import check_cluster_id_exists

from ._common import ClusterContainers, existing_cluster_ids
from ._options import node_transport_option


def _destroy_cluster(
    cluster_id: str,
    transport: Transport,
    enable_spinner: bool,
) -> None:
    """
    Destroy a cluster.

    Args:
        cluster_id: The ID of the cluster.
        transport: The transport to use for any communication with the cluster.
        enable_spinner: Whether to enable the spinner animation.
    """
    with Halo(enabled=enable_spinner):
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
@enable_spinner_option
def destroy_list(
    cluster_ids: List[str],
    transport: Transport,
    enable_spinner: bool,
) -> None:
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

        _destroy_cluster(
            cluster_id=cluster_id,
            transport=transport,
            enable_spinner=enable_spinner,
        )
        click.echo(cluster_id)


@click.command('destroy')
@existing_cluster_id_option
@node_transport_option
@enable_spinner_option
def destroy(
    cluster_id: str,
    transport: Transport,
    enable_spinner: bool,
) -> None:
    """
    Destroy a cluster.
    """
    _destroy_cluster(
        cluster_id=cluster_id,
        transport=transport,
        enable_spinner=enable_spinner,
    )
    click.echo(cluster_id)
