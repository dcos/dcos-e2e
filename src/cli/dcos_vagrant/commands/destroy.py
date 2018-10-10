"""
Tools for destroying clusters.
"""

from typing import List

import click
import click_spinner

from cli.common.options import existing_cluster_id_option
from cli.common.utils import check_cluster_id_exists

from ._common import ClusterVMs, existing_cluster_ids


@click.command('destroy-list')
@click.argument(
    'cluster_ids',
    nargs=-1,
    type=str,
)
@click.pass_context
def destroy_list(
    ctx: click.core.Context,
    cluster_ids: List[str],
) -> None:
    """
    Destroy clusters.

    To destroy all clusters, run ``dcos-vagrant destroy $(dcos-vagrant list)``.
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
        )


@click.command('destroy')
@existing_cluster_id_option
def destroy(cluster_id: str) -> None:
    """
    Destroy a cluster.
    """
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    cluster_vms = ClusterVMs(cluster_id=cluster_id)
    with click_spinner.spinner():
        cluster_vms.destroy()
    click.echo(cluster_id)
