"""
Common commands and command factories.
"""

import click


def list_clusters_command_factory(
    existing_cluster_ids_func: Callable[[], Set[str]],
) -> Callable[None, None]:
    """
    Return a Click command for listing clusters.

    Args:
        existing_cluster_ids_func: A function which returns existing cluster
            IDs.
    """

    @click.command('list')
    def list_clusters() -> None:
        """
        List all clusters.
        """
        for cluster_id in existing_cluster_ids():
            click.echo(cluster_id)

    return list_clusters
