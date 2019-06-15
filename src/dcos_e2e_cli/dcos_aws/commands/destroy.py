"""
Tools for destroying clusters.
"""

from typing import List

import click
from halo import Halo

from dcos_e2e_cli.common.options import (
    enable_spinner_option,
    existing_cluster_id_option,
    verbosity_option,
)
from dcos_e2e_cli.common.utils import check_cluster_id_exists

from ._common import ClusterInstances, existing_cluster_ids
from ._options import aws_region_option


def destroy_cluster(
    cluster_id: str,
    enable_spinner: bool,
    aws_region: str,
) -> None:
    """
    Destroy a cluster.

    Args:
        cluster_id: The ID of the cluster.
        enable_spinner: Whether to enable the spinner animation.
        aws_region: The region the cluster is in.
    """
    with Halo(enabled=enable_spinner):
        check_cluster_id_exists(
            new_cluster_id=cluster_id,
            existing_cluster_ids=existing_cluster_ids(aws_region=aws_region),
        )
        cluster_vms = ClusterInstances(
            cluster_id=cluster_id,
            aws_region=aws_region,
        )
        cluster_vms.destroy()


@click.command('destroy-list')
@aws_region_option
@enable_spinner_option
@verbosity_option
@click.argument('cluster_ids', nargs=-1, type=str)
def destroy_list(
    cluster_ids: List[str],
    enable_spinner: bool,
    aws_region: str,
) -> None:
    """
    Destroy clusters.

    To destroy all clusters, run
    ``minidcos aws destroy $(minidcos aws list)``.
    """
    for cluster_id in cluster_ids:
        if cluster_id in existing_cluster_ids(aws_region=aws_region):
            destroy_cluster(
                enable_spinner=enable_spinner,
                cluster_id=cluster_id,
                aws_region=aws_region,
            )
            click.echo(cluster_id)
        else:
            warning = 'Cluster "{cluster_id}" does not exist'.format(
                cluster_id=cluster_id,
            )
            click.echo(warning, err=True)
            continue


@click.command('destroy')
@enable_spinner_option
@aws_region_option
@verbosity_option
@existing_cluster_id_option
def destroy(cluster_id: str, enable_spinner: bool, aws_region: str) -> None:
    """
    Destroy a cluster.
    """
    destroy_cluster(
        cluster_id=cluster_id,
        enable_spinner=enable_spinner,
        aws_region=aws_region,
    )
    click.echo(cluster_id)
