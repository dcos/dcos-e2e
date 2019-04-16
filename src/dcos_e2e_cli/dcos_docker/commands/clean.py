"""
Clean all Docker containers, volumes etc. from using the Docker backend.
"""

import click

from dcos_e2e.backends import Docker
from dcos_e2e.docker_utils import DockerLoopbackVolume
from dcos_e2e_cli.common.options import verbosity_option

from ._common import (
    NODE_TYPE_LABEL_KEY,
    NODE_TYPE_LOOPBACK_SIDECAR_LABEL_VALUE,
    docker_client,
)


@click.command('clean')
@verbosity_option
def clean() -> None:
    """
    Remove containers, volumes and networks created by this tool.
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
        DockerLoopbackVolume.destroy(container=loopback_sidecar)

    node_filters = {'name': Docker().container_name_prefix}
    network_filters = {'name': Docker().container_name_prefix}

    node_containers = client.containers.list(filters=node_filters, all=True)

    for container in node_containers:
        container.stop()
        container.remove(v=True)

    networks = client.networks.list(filters=network_filters)
    for network in networks:
        network.remove()
