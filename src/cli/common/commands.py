"""
Common commands and command factories.
"""

from pathlib import Path

import click
import requests


@click.command('download-artifact')
@click.option(
    '--dcos-version',
    type=str,
    default='stable',
    show_default=True,
    help=(
        'The DC/OS Open Source artifact version to download. '
        'This can be in one of the following formats: '
        '``stable``, '
        '``testing/master``, '
        '``testing/<DC/OS MAJOR RELEASE>``, '
        '``stable/<DC/OS MINOR RELEASE>``, '
        '``testing/pull/<GITHUB-PR-NUMBER>``.\n'
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

    if path.is_dir():
        path = path / 'dcos_generate_config.sh'

    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    # See
    # https://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py

    stream = requests.get(url, stream=True)
    assert stream.ok
    content_length = int(stream.headers['Content-Length'])
    total_written = 0
    chunk_size = 1024
    # See http://click.pocoo.org/6/arguments/#file-args for parameter
    # information
    with click.open_file(
        filename=str(path),
        mode='wb',
        atomic=True,
        lazy=True,
    ) as file_descriptor:
        content_iter = stream.iter_content(chunk_size=chunk_size)
        with click.progressbar(  # type: ignore
            content_iter,
            length=content_length / chunk_size,
            label=label,
        ) as progress_bar:
            for chunk in progress_bar:
                # Filter out keep-alive new chunks.
                if chunk:
                    total_written += len(chunk)
                    file_descriptor.write(chunk)  # type: ignore

    message = (
        'Downloaded {total_written} bytes. '
        'Expected {content_length} bytes.'
    ).format(
        total_written=total_written,
        content_length=content_length,
    )
    assert total_written == content_length, message
