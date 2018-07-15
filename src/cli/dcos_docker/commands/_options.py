"""
Common options for ``dcos-docker`` commands.
"""

from typing import Callable

import click

from cli.common.options import make_existing_cluster_id_option
from dcos_e2e.node import Transport

from ._common import existing_cluster_ids


def existing_cluster_id_option(command: Callable[..., None],
                               ) -> Callable[..., None]:
    """
    An option decorator for one Cluster ID.
    """
    existing_id_option = make_existing_cluster_id_option(
        existing_cluster_ids_func=existing_cluster_ids,
    )

    return existing_id_option(command)


def node_transport_option(command: Callable[..., None],
                          ) -> Callable[..., None]:
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
        envvar='DCOS_DOCKER_TRANSPORT',
        help=(
            'The communication transport to use. '
            'On macOS the SSH transport requires IP routing to be set up. '
            'See "dcos-docker setup-mac-network".'
            'It also requires the "ssh" command to be available. '
            'This can be provided by setting the `DCOS_DOCKER_TRANSPORT` '
            'environment variable.'
        ),
    )(command)  # type: Callable[..., None]
    return function
