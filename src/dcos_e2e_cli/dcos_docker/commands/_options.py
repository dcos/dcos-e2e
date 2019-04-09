"""
Common options for ``minidcos docker`` commands.
"""

from typing import Callable

import click

from dcos_e2e.node import Transport


def node_transport_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for node transport options.
    """
    transports = {
        'ssh': Transport.SSH,
        'docker-exec': Transport.DOCKER_EXEC,
    }

    function = click.option(
        '--transport',
        type=click.Choice(sorted(transports.keys())),
        callback=lambda ctx, param, value: transports[str(value)],
        default='docker-exec',
        show_default=True,
        envvar='MINIDCOS_DOCKER_TRANSPORT',
        help=(
            'The communication transport to use. '
            'On macOS the SSH transport requires IP routing to be set up. '
            'See "minidcos docker setup-mac-network". '
            'It also requires the "ssh" command to be available. '
            'This can be provided by setting the `MINIDCOS_DOCKER_TRANSPORT` '
            'environment variable. '
            'When using a TTY, different transports may use different line '
            'endings.'
        ),
    )(command)  # type: Callable[..., None]
    return function


def node_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for choosing a node.
    """
    function = click.option(
        '--node',
        type=str,
        default=('master_0', ),
        show_default=True,
        multiple=True,
        help=(
            'A reference to a particular node to run the command on. '
            'This can be one of: '
            'The node\'s IP address, '
            'the node\'s Docker container name, '
            'the node\'s Docker container ID, '
            'a reference in the format "<role>_<number>". '
            'These details be seen with ``minidcos docker inspect``.'
        ),
    )(command)  # type: Callable[..., None]
    return function
