"""
Tools for destroying sidecar containers.
"""

import click
from halo import Halo

from dcos_e2e.docker_utils import DockerLoopbackVolume
from dcos_e2e_cli.common.options import enable_spinner_option

from ._loopback_sidecars import loopback_sidecars_by_name


@click.command('destroy-loopback-sidecar')
@enable_spinner_option
@click.argument('name', type=str)
def destroy_loopback_sidecar(enable_spinner: bool, name: str) -> None:
    """
    Destroy a loopback sidecar.
    """
    loopback_sidecars = loopback_sidecars_by_name(name=name)

    if not loopback_sidecars:
        message = 'Loopback sidecar "{name}" does not exist'.format(
            name=name,
        )
        raise click.BadParameter(message)

    [loopback_sidecar] = loopback_sidecars
    with Halo(enabled=enable_spinner):
        DockerLoopbackVolume.destroy(container=loopback_sidecar)
