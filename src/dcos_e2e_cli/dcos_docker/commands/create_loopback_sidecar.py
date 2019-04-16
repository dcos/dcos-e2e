"""
Tools for creating sidecar containers.
"""

import click

from dcos_e2e.docker_utils import DockerLoopbackVolume

from ._common import (
    NODE_TYPE_LABEL_KEY,
    NODE_TYPE_LOOPBACK_SIDECAR_LABEL_VALUE,
    SIDECAR_NAME_LABEL_KEY,
)
from ._loopback_sidecars import loopback_sidecars_by_name


@click.command('create-loopback-sidecar')
@click.option(
    '--size',
    type=click.IntRange(min=1),
    default=256,
    help='Size (in Megabytes) of the block device.',
)
@click.argument('name', type=str, required=True)
def create_loopback_sidecar(size: int, name: str) -> None:
    """
    Create a loopback sidecar.

    A loopback sidecar provides a loopback device that points to a
    (unformatted) block device.
    """

    if loopback_sidecars_by_name(name=name):
        message = 'Loopback sidecar "{name}" already exists'.format(
            name=name,
        )
        raise click.BadParameter(message)

    loopback_volume = DockerLoopbackVolume(
        size_megabytes=size,
        labels={
            NODE_TYPE_LABEL_KEY: NODE_TYPE_LOOPBACK_SIDECAR_LABEL_VALUE,
            SIDECAR_NAME_LABEL_KEY: name,
        },
    )

    click.echo(loopback_volume.path)
