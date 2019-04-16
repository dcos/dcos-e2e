"""
Tools for sending files to cluster nodes.
"""

from pathlib import Path
from typing import Tuple

import click

from dcos_e2e.node import Transport
from dcos_e2e_cli.common.nodes import get_nodes
from dcos_e2e_cli.common.options import (
    existing_cluster_id_option,
    verbosity_option,
)
from dcos_e2e_cli.common.utils import (
    check_cluster_id_exists,
    command_path,
    set_logging,
)

from ._common import ClusterContainers, existing_cluster_ids
from ._nodes import node_option
from ._options import node_transport_option
from .inspect_cluster import inspect_cluster


@click.command('send-file')
@existing_cluster_id_option
@node_transport_option
@node_option
@verbosity_option
@click.argument('source', type=click.Path(exists=True))
@click.argument('destination')
@click.pass_context
def send_file(
    ctx: click.core.Context,
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

    inspect_command_name = command_path(
        sibling_ctx=ctx,
        command=inspect_cluster,
    )

    hosts = get_nodes(
        cluster_id=cluster_id,
        cluster_representation=cluster_containers,
        node_references=node,
        inspect_command_name=inspect_command_name,
    )

    for host in hosts:
        host.send_file(
            local_path=Path(source),
            remote_path=Path(destination),
            transport=transport,
            sudo=False,
        )
