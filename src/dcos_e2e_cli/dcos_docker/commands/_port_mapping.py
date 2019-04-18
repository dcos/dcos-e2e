"""
Helpers for managing port mapping.
"""

from typing import Callable, Dict, Tuple, Union

import click


def _validate_port_map(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Tuple[str],
) -> Dict[str, int]:
    """
    Turn port map strings into a Dict that ``docker-py`` can use.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    ports = {}  # type: Dict[str, int]
    for ports_definition in value:
        parts = ports_definition.split(':')

        # Consider support the full docker syntax.
        # https://docs.docker.com/engine/reference/run/#expose-incoming-ports
        if len(parts) != 2:
            message = (
                '"{ports_definition}" is not a valid port map. '
                'Please follow this syntax: <HOST_PORT>:<CONTAINER_PORT>'
            ).format(ports_definition=ports_definition)
            raise click.BadParameter(message=message)

        host_port, container_port = parts
        if not host_port.isdigit():
            message = 'Host port "{host_port}" is not an integer.'.format(
                host_port=host_port,
            )
            raise click.BadParameter(message=message)
        if not container_port.isdigit():
            message = ('Container port "{container_port}" is an integer.'
                       ).format(container_port=container_port)
            raise click.BadParameter(message=message)
        if int(host_port) < 0 or int(host_port) > 65535:
            message = ('Host port "{host_port}" is not a valid port number.'
                       ).format(host_port=host_port)
            raise click.BadParameter(message=message)
        if int(container_port) < 0 or int(container_port) > 65535:
            message = (
                'Container port "{container_port}" is not a valid port number.'
            ).format(container_port=container_port)
            raise click.BadParameter(message=message)

        key = container_port + '/tcp'
        if key in ports:
            message = (
                'Container port "{container_port}" specified multiple times.'
            ).format(container_port=container_port)
            raise click.BadParameter(message=message)

        ports[key] = int(host_port)
    return ports


def one_master_host_port_map_option(command: Callable[..., None],
                                    ) -> Callable[..., None]:
    """
    An option decorator for choosing Docker port mappings.
    """
    function = click.option(
        '--one-master-host-port-map',
        type=str,
        callback=_validate_port_map,
        help=(
            'Publish a container port of one master node to the host. '
            'Only Transmission Control Protocol is supported currently. '
            'The syntax is <HOST_PORT>:<CONTAINER_PORT>'
        ),
        multiple=True,
    )(command)  # type: Callable[..., None]
    return function
