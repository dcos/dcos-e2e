"""
Helpers for managing Docker network settings.
"""

from typing import Callable, Optional, Union

import click
import docker
from docker.models.networks import Network

from ._common import docker_client


def _validate_docker_network(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Optional[Union[int, bool, str]],
) -> Network:
    """
    Validate that a given network name is an existing Docker network name.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass
    client = docker_client()
    try:
        return client.networks.get(network_id=value)
    except docker.errors.NotFound:
        message = (
            'No such Docker network with the name "{value}".\n'
            'Docker networks are:\n{networks}'
        ).format(
            value=value,
            networks='\n'.join(
                [network.name for network in client.networks.list()],
            ),
        )
        raise click.BadParameter(message=message)


def docker_network_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for choosing a Docker network.
    """
    click_option_function = click.option(
        '--network',
        type=str,
        default='bridge',
        help=(
            'The Docker network containers will be connected to.'
            'It may not be possible to SSH to containers on a custom network '
            'on macOS. '
        ),
        callback=_validate_docker_network,
    )  # type: Callable[[Callable[..., None]], Callable[..., None]]
    function = click_option_function(command)  # type: Callable[..., None]
    return function
