"""
Tools for listing sidecar containers.
"""

import click
import click_spinner

from dcos_e2e.docker_utils import DockerLoopbackVolume

from ._common import loopback_sidecars_by_name


@click.command('destroy-loopback-sidecar')
@click.argument('name', type=str)
def destroy_loopback_sidecar(name: str) -> None:
    """
    Destroy a loopback sidecar.
    """
    loopback_sidecars = loopback_sidecars_by_name(name=name)

    if not loopback_sidecars:
        message = 'Loopback sidecar "{name}" does not exist'.format(
            name=name,
        )
        raise click.BadParameter(message)

    (loopback_sidecar, ) = loopback_sidecars
    with click_spinner.spinner():
        DockerLoopbackVolume.destroy(container=loopback_sidecar)
