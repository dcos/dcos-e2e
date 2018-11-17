"""
Common commands and command factories.
"""

from pathlib import Path

import click
import requests
from tqdm import tqdm


@click.command('download-installer')
@click.option(
    '--dcos-version',
    type=str,
    default='stable',
    show_default=True,
    help=(
        'The DC/OS Open Source installer version to download. '
        'This can be in one of the following formats: '
        '``stable``, '
        '``testing/master``, '
        '``testing/<DC/OS MAJOR RELEASE>``, '
        '``stable/<DC/OS MINOR RELEASE>``, '
        '``testing/pull/<GITHUB-PR-NUMBER>``.\n'
        'See https://dcos.io/releases/ for available releases.'
        '\n'
        'If an HTTP or HTTPS URL is given, that is downloaded.'
    ),
)
@click.option(
    '--download-path',
    type=str,
    default='./dcos_generate_config.sh',
    show_default=True,
    help='The path to download an installer to.',
)
@click.pass_context
def download_installer(
    ctx: click.core.Context,
    dcos_version: str,
    download_path: str,
) -> None:
    """
    Download a DC/OS Open Source installer.

    For DC/OS Enterprise installers, contact your sales representative.
    """
    path = Path(download_path)
    path.parent.mkdir(exist_ok=True, parents=True)
    path = path.parent.resolve() / path.name

    click.echo('Downloading to {path}.'.format(path=path))

    if dcos_version.startswith('http'):
        url = dcos_version
    else:
        base_url = 'https://downloads.dcos.io/dcos/'
        url = base_url + dcos_version + '/dcos_generate_config.sh'

    head_resp = requests.head(url)
    if not head_resp.ok:
        message = 'Cannot download installer from {url}.'.format(url=url)
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
    # See http://click.pocoo.org/7/arguments/#file-args for parameter
    # information.
    content_iter = stream.iter_content(chunk_size=chunk_size)
    progress_bar = tqdm(
        iterable=content_iter,
        total=content_length / chunk_size,
        dynamic_ncols=True,
        bar_format='{l_bar}{bar}',
        unit_scale=None,
    )
    with click.open_file(
        filename=str(path),
        mode='wb',
        atomic=True,
        lazy=True,
    ) as file_descriptor:
        for chunk in progress_bar:
            # Enable at the start of each chunk, disable at the end, to avoid
            # showing statistics at the end.
            progress_bar.disable = False
            # Filter out keep-alive new chunks.
            if chunk:
                total_written += len(chunk)
                file_descriptor.write(chunk)  # type: ignore
            progress_bar.disable = True

    message = (
        'Downloaded {total_written} bytes. '
        'Expected {content_length} bytes.'
    ).format(
        total_written=total_written,
        content_length=content_length,
    )
    assert total_written == content_length, message
