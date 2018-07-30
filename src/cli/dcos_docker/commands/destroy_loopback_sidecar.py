"""
Tools for destroying sidecar containers.
"""

import click
import click_spinner

from dcos_e2e.docker_utils import DockerLoopbackVolume

from ._common import loopback_sidecar_by_name


@click.command('destroy-loopback-sidecar')
@click.argument(
    'name',
    type=str,
)
def destroy_loopback_sidecar(name: str) -> None:
    """
    Destroy a loopback sidecar.
    """
    loopback_sidecar = loopback_sidecar_by_name(name)

    if loopback_sidecar is None:
        message = 'Loopback sidecar "{name}" does not exist'.format(
            name=name,
        )
        raise click.BadParameter(message)

    with click_spinner.spinner():
        DockerLoopbackVolume.destroy(loopback_sidecar)
