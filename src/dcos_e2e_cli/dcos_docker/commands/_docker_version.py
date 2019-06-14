"""
Docker Version Option
"""

from typing import Callable, Union

import click

from dcos_e2e.docker_versions import DockerVersion

_DOCKER_VERSIONS = {
    '1.11.2': DockerVersion.v1_11_2,
    '1.13.1': DockerVersion.v1_13_1,
    '17.12.1-ce': DockerVersion.v17_12_1_ce,
    '18.06.3-ce': DockerVersion.v18_06_3_ce,
}


def _get_docker_version(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: str,
) -> DockerVersion:
    """
    Get the chosen Docker version.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    return _DOCKER_VERSIONS[value]


def docker_version_option(command: Callable[..., None],
                          ) -> Callable[..., None]:
    """
    Option for choosing the Docker version to use inside the container.
    """
    function = click.option(
        '--docker-version',
        type=click.Choice(sorted(_DOCKER_VERSIONS.keys())),
        default='18.06.3-ce',
        envvar='MINIDCOS_NODE_DOCKER_VERSION',
        show_default=True,
        help=(
            'The Docker version to install on the nodes. '
            'This can be provided by setting the '
            '`MINIDCOS_NODE_DOCKER_VERSION` environment variable.'
        ),
        callback=_get_docker_version,
    )(command)  # type: Callable[..., None]
    return function
