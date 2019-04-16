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

from ._common import ClusterInstances, existing_cluster_ids
from ._options import aws_region_option


@click.command('inspect')
@existing_cluster_id_option
@aws_region_option
@verbosity_option
def inspect_cluster(cluster_id: str, aws_region: str) -> None:
    """
    Show cluster details.
    """
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(aws_region=aws_region),
    )
    cluster_instances = ClusterInstances(
        cluster_id=cluster_id,
        aws_region=aws_region,
    )
    show_cluster_details(
        cluster_id=cluster_id,
        cluster_representation=cluster_instances,
    )
