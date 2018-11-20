"""
Tools for syncing code to a cluster.
"""

from pathlib import Path

import click

from dcos_e2e.node import Transport
from dcos_e2e_cli.common.arguments import dcos_checkout_dir_argument
from dcos_e2e_cli.common.options import (
    existing_cluster_id_option,
    verbosity_option,
)
from dcos_e2e_cli.common.sync import SYNC_HELP, sync_code_to_masters
from dcos_e2e_cli.common.utils import check_cluster_id_exists, set_logging

from ._common import ClusterContainers, existing_cluster_ids
from ._options import node_transport_option


@click.command('sync', help=SYNC_HELP)
@existing_cluster_id_option
@dcos_checkout_dir_argument
@node_transport_option
@verbosity_option
def sync_code(
    cluster_id: str,
    dcos_checkout_dir: str,
    transport: Transport,
    verbose: int,
) -> None:
    """
    Sync files from a DC/OS checkout to master nodes.
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
    cluster = cluster_containers.cluster
    sync_code_to_masters(
        cluster=cluster,
        dcos_checkout_dir=Path(dcos_checkout_dir),
        dcos_variant=cluster_containers.dcos_variant,
    )
