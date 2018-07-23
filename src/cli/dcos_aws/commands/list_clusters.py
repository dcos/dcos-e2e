"""
Tools for listing clusters.
"""

import click

from ._common import existing_cluster_ids
from ._options import aws_region_option


@click.command('list')
@aws_region_option
def list_clusters(aws_region: str) -> None:
    """
    List all clusters.
    """
    for cluster_id in existing_cluster_ids(aws_region=aws_region):
        click.echo(cluster_id)
