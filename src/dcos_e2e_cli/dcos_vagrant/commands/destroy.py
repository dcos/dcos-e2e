"""
Tools for destroying clusters.
"""

import sys
from typing import List

import click
from halo import Halo

from dcos_e2e_cli.common.options import existing_cluster_id_option
from dcos_e2e_cli.common.utils import check_cluster_id_exists

from ._common import ClusterVMs, existing_cluster_ids


@Halo(enabled=sys.stdout.isatty())
def destroy_cluster(cluster_id: str) -> None:
    """
    Destroy a cluster.

    Args:
        cluster_id: The ID of the cluster.
    """
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    cluster_vms = ClusterVMs(cluster_id=cluster_id)
    cluster_vms.destroy()


@click.command('destroy-list')
@click.argument('cluster_ids', nargs=-1, type=str)
def destroy_list(cluster_ids: List[str]) -> None:
    """
    Destroy clusters.

    To destroy all clusters, run
    ``minidcos vagrant destroy $(minidcos vagrant list)``.
    """
    for cluster_id in cluster_ids:
        if cluster_id in existing_cluster_ids():
            destroy_cluster(cluster_id=cluster_id)
            click.echo(cluster_id)
        else:
            warning = 'Cluster "{cluster_id}" does not exist'.format(
                cluster_id=cluster_id,
            )
            click.echo(warning, err=True)
            continue


@click.command('destroy')
@existing_cluster_id_option
def destroy(cluster_id: str) -> None:
    """
    Destroy a cluster.
    """
    destroy_cluster(cluster_id=cluster_id)
    click.echo(cluster_id)
