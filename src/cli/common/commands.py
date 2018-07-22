"""
Common commands and command factories.
"""

from pathlib import Path
from typing import Callable, Set

import click
import requests


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
@click.option(
    '--dcos-version',
    type=str,
    default='stable',
    show_default=True,
    help=(
        'The DC/OS Open Source artifact version to download. '
        'This can be in one of the following formats: '
        '"stable", testing/master", "testing/<DC/OS MAJOR RELEASE>", '
        '"stable/<DC/OS MINOR RELEASE>", "testing/pull/<GITHUB-PR-NUMBER>".\n'
        'See https://dcos.io/releases/ for available releases.'
    ),
)
@click.option(
    '--download-path',
    type=str,
    default='/tmp/dcos_generate_config.sh',
    show_default=True,
    help='The path to download a release artifact to.',
)
@click.pass_context
def download_artifact(
    ctx: click.core.Context,
    dcos_version: str,
    download_path: str,
) -> None:
    """
    Download a DC/OS Open Source artifact.

    For DC/OS Enterprise release artifacts, contact your sales representative.
    """
    path = Path(download_path)
    label = 'Downloading to ' + str(path)
    base_url = 'https://downloads.dcos.io/dcos/'
    url = base_url + dcos_version + '/dcos_generate_config.sh'
    head_resp = requests.head(url)
    if not head_resp.ok:
        message = 'Cannot download artifact from {url}.'.format(url=url)
        ctx.fail(message=message)

    # TODO make parents
    # TODO if directory given, add filename to end
    import pdb; pdb.set_trace()
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
