"""
Tools for sending files to cluster nodes.
"""

from pathlib import Path
from typing import Tuple

import click

from dcos_e2e.node import Transport
from dcos_e2e_cli.common.options import (
    existing_cluster_id_option,
    verbosity_option,
)
from dcos_e2e_cli.common.utils import check_cluster_id_exists, set_logging

from ._common import ClusterContainers, existing_cluster_ids
from ._nodes import get_node, node_option
from ._options import node_transport_option


@click.command('send-file')
@existing_cluster_id_option
@node_transport_option
@node_option
@verbosity_option
@click.argument('source', type=click.Path(exists=True))
@click.argument('destination')
def send_file(
    cluster_id: str,
    node: Tuple[str],
    transport: Transport,
    verbose: int,
    source: str,
    destination: str,
) -> None:
    """
    Send a file to a node or multiple nodes.
    """
    set_logging(verbosity_level=verbose)
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )

    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        transport=transport,
    )
    cluster_containers.cluster

    hosts = set([])
    for node_reference in node:
        host = get_node(
            cluster_containers=cluster_containers,
            node_reference=node_reference,
        )
        if host is None:
            message = (
                'No such node in cluster "{cluster_id}" with IP address, '
                'Docker container name, Docker container ID or node reference '
                '"{node_reference}". '
                'Node references can be seen with ``minidcos docker inspect``.'
            ).format(
                cluster_id=cluster_id,
                node_reference=node_reference,
            )
            raise click.BadParameter(message=message)

        hosts.add(host)

    for host in hosts:
        host.send_file(
            local_path=Path(source),
            remote_path=Path(destination),
            transport=transport,
            sudo=False,
        )
