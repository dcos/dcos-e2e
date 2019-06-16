"""
Tools for sending files to cluster nodes.
"""

from pathlib import Path
from typing import Tuple

import click
import click_pathlib

from dcos_e2e.node import Transport
from dcos_e2e_cli.common.nodes import get_nodes
from dcos_e2e_cli.common.options import (
    existing_cluster_id_option,
    verbosity_option,
)
from dcos_e2e_cli.common.utils import check_cluster_id_exists, command_path

from ._common import ClusterInstances, existing_cluster_ids
from ._nodes import node_option
from ._options import aws_region_option
from .inspect_cluster import inspect_cluster


@click.command('send-file')
@existing_cluster_id_option
@node_option
@verbosity_option
@aws_region_option
@click.argument('source', type=click_pathlib.Path(exists=True))
@click.argument('destination', type=click_pathlib.Path())
@click.pass_context
def send_file(
    ctx: click.core.Context,
    cluster_id: str,
    node: Tuple[str],
    source: Path,
    destination: Path,
    aws_region: str,
) -> None:
    """
    Send a file to a node or multiple nodes.
    """
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(aws_region=aws_region),
    )
    cluster_instances = ClusterInstances(
        cluster_id=cluster_id,
        aws_region=aws_region,
    )

    inspect_command_name = command_path(
        sibling_ctx=ctx,
        command=inspect_cluster,
    )

    hosts = get_nodes(
        cluster_id=cluster_id,
        cluster_representation=cluster_instances,
        node_references=node,
        inspect_command_name=inspect_command_name,
    )

    for host in hosts:
        host.send_file(
            local_path=source,
            remote_path=destination,
            transport=Transport.SSH,
            sudo=True,
        )
