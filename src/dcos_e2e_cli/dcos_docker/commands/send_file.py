from typing import Tuple

import click

from dcos_e2e.node import Transport
from dcos_e2e_cli.common.options import (
    existing_cluster_id_option,
    verbosity_option,
)


@click.command('destroy')
@existing_cluster_id_option
@node_transport_option
@verbosity_option
def send_file(
    cluster_id: str, node: Tuple[str], transport: Transport, verbose: int
) -> None:
    """
    Send a file to a node.
    """
