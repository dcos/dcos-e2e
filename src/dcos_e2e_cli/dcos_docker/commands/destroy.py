"""
Tools for destroying clusters.
"""

from typing import List

import click
import click_spinner

from dcos_e2e.node import Transport
from dcos_e2e_cli.common.options import existing_cluster_id_option
from dcos_e2e_cli.common.utils import check_cluster_id_exists

from ._common import ClusterContainers, existing_cluster_ids
from ._options import node_transport_option


@click.command('destroy-list')
@click.argument(
    'cluster_ids',
    nargs=-1,
    type=str,
)
@node_transport_option
@click.pass_context
def destroy_list(
    ctx: click.core.Context,
    cluster_ids: List[str],
    transport: Transport,
) -> None:
    """
    Destroy clusters.

    To destroy all clusters, run ``dcos-docker destroy $(dcos-docker list)``.
    """
    for cluster_id in cluster_ids:
        if cluster_id not in existing_cluster_ids():
            warning = 'Cluster "{cluster_id}" does not exist'.format(
                cluster_id=cluster_id,
            )
            click.echo(warning, err=True)
            continue

        ctx.invoke(
            destroy,
            cluster_id=cluster_id,
            transport=transport,
        )


@click.command('destroy')
@existing_cluster_id_option
@node_transport_option
def destroy(cluster_id: str, transport: Transport) -> None:
    """
    Destroy a cluster.
    """
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        transport=transport,
    )
    with click_spinner.spinner():
        cluster_containers.destroy()
    click.echo(cluster_id)
