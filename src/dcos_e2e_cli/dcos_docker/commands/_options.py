"""
Common options for ``minidcos docker`` commands.
"""

from typing import Callable

import click

from dcos_e2e.backends import Docker
from dcos_e2e.node import Transport


def node_transport_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for node transport options.
    """
    transports = {
        'ssh': Transport.SSH,
        'docker-exec': Transport.DOCKER_EXEC,
    }

    backend_default = Docker().transport
    [default_option] = [
        transport for transport in transports
        if transports[transport] == backend_default
    ]

    function = click.option(
        '--transport',
        type=click.Choice(sorted(transports.keys())),
        callback=lambda ctx, param, value: transports[value],
        default=default_option,
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


def wait_for_dcos_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for waiting for DC/OS to be up.
    """
    function = click.option(
        '--wait-for-dcos',
        is_flag=True,
        help=(
            'Wait for DC/OS after creating the cluster. '
            'This is equivalent to using "minidcos docker wait" after this '
            'command. '
            '"minidcos docker wait" has various options available and so may '
            'be more appropriate for your use case. '
            'If the chosen transport is "docker-exec", this will skip HTTP '
            'checks and so the cluster may not be fully ready.'
        ),
    )(command)  # type: Callable[..., None]
    return function
