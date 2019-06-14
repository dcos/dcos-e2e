"""
Docker Storage Driver Option
"""

from typing import Callable, Optional, Union

import click

from dcos_e2e.docker_storage_drivers import DockerStorageDriver

DOCKER_STORAGE_DRIVERS = {
    'aufs': DockerStorageDriver.AUFS,
    'overlay': DockerStorageDriver.OVERLAY,
    'overlay2': DockerStorageDriver.OVERLAY_2,
    'auto': None,
}


def _get_docker_storage_driver(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: str,
) -> Optional[DockerStorageDriver]:
    """
    Get the chosen Docker storage driver.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    return DOCKER_STORAGE_DRIVERS[value]


def docker_storage_driver_option(command: Callable[..., None],
                                 ) -> Callable[..., None]:
    """
    Option for choosing the Docker storage driver to use inside the container.
    """
    function = click.option(
        '--docker-storage-driver',
        type=click.Choice(sorted(DOCKER_STORAGE_DRIVERS.keys())),
        default='auto',
        show_default=True,
        help=(
            'The storage driver to use for Docker in Docker. '
            "By default this uses the host's driver."
        ),
        callback=_get_docker_storage_driver,
    )(command)  # type: Callable[..., None]
    return function
