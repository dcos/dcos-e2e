"""
Tools for listing clusters.
"""

import click

from ._common import existing_cluster_ids


@click.command('list')
def list_clusters() -> None:
    """
    List all clusters.
    """
    for cluster_id in existing_cluster_ids():
        click.echo(cluster_id)
