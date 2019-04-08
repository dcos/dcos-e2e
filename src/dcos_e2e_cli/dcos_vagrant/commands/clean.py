"""
Clean all Docker containers, volumes etc. from using the Docker backend.
"""

import click

from dcos_e2e_cli.common.options import verbosity_option
from dcos_e2e_cli.common.utils import set_logging

from ._common import (
    CLUSTER_ID_DESCRIPTION_KEY,
)

@click.command('clean')
@click.option(
    '--keep-running',
    is_flag=True,
    default=True,
    help='Do not destroy running VMs.',
)
@verbosity_option
def clean(verbose: int, keep_running: bool) -> None:
    """
    Remove VMs created by this tool.

    This is useful in removing paused and aborted VMs.
    VMs are aborted when the host is shut down.
    """
    set_logging(verbosity_level=verbose)

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
