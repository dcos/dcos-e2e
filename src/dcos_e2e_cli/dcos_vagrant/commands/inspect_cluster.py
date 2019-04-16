"""
Tools for inspecting existing clusters.
"""

import click

from dcos_e2e_cli.common.inspect_cluster import show_cluster_details
from dcos_e2e_cli.common.options import (
    existing_cluster_id_option,
    verbosity_option,
)
from dcos_e2e_cli.common.utils import check_cluster_id_exists

from ._common import ClusterVMs, existing_cluster_ids


@click.command('inspect')
@existing_cluster_id_option
@verbosity_option
def inspect_cluster(cluster_id: str) -> None:
    """
    Show cluster details.
    """
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    cluster_vms = ClusterVMs(cluster_id=cluster_id)
    show_cluster_details(
        cluster_id=cluster_id,
        cluster_representation=cluster_vms,
    )
