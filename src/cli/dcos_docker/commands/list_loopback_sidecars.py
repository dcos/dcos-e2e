"""
Tools for destroying sidecar containers.
"""

import click
import click_spinner

from dcos_e2e.docker_utils import DockerLoopbackVolume

from ._common import docker_client, NODE_TYPE_LABEL_KEY, NODE_TYPE_LOOPBACK_SIDECAR_LABEL_VALUE, SIDECAR_NAME_LABEL_KEY


@click.command('list-loopback-sidecars')
def list_loopback_sidecars() -> None:
    """
    List loopback sidecars.
    """
    client = docker_client()
    filters = {
        'label': [
            '{key}={value}'.format(
                key=NODE_TYPE_LABEL_KEY,
                value=NODE_TYPE_LOOPBACK_SIDECAR_LABEL_VALUE,
            ),
        ],
    }
    loopback_sidecars = client.containers.list(filters=filters)
    for loopback_sidecar in loopback_sidecars:
        name = loopback_sidecar.labels[SIDECAR_NAME_LABEL_KEY]
        click.echo(name)
