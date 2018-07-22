"""
Common commands and command factories.
"""

from typing import Callable, Set

import click


def list_clusters_command_factory(
    existing_cluster_ids_func: Callable[[], Set[str]],
) -> Callable[[None], None]:
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
        for cluster_id in existing_cluster_ids_func():
            click.echo(cluster_id)

    list_clusters_func = list_clusters  # type: Callable[[None], None]
    return list_clusters_func


@click.command('download-artifact')
def download_artifact() -> None:
    """
    List all clusters.
    """
    label = 'Downloading to ' + str(path)
    stream = requests.get(url, stream=True)
    content_length = int(stream.headers['Content-Length'])
    chunk_size = 100 * 1024
    with click.open_file(str(path), 'wb') as file_descriptor:
        content_iter = stream.iter_content(chunk_size=chunk_size)
        with click.progressbar(  # type: ignore
            content_iter,
            length=content_length / chunk_size,
            label=label,
        ) as progress_bar:
            for chunk in progress_bar:
                if chunk:
                    file_descriptor.write(chunk)  # type: ignore
                    file_descriptor.flush()  # type: ignore
