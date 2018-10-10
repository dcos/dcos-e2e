"""
Tools for syncing code to a cluster.
"""

from pathlib import Path

import click
from cli.common.arguments import dcos_checkout_dir_argument
from cli.common.options import existing_cluster_id_option, verbosity_option
from cli.common.sync import sync_code_to_masters
from cli.common.utils import check_cluster_id_exists, set_logging

from ._common import ClusterInstances, existing_cluster_ids
from ._options import aws_region_option


@click.command('sync')
@existing_cluster_id_option
@dcos_checkout_dir_argument
@aws_region_option
@verbosity_option
def sync_code(
    cluster_id: str,
    dcos_checkout_dir: str,
    aws_region: str,
    verbose: int,
) -> None:
    """
    Sync files from a DC/OS checkout to master nodes.

    This syncs integration test files and bootstrap files.

    ``DCOS_CHECKOUT_DIR`` should be set to the path of clone of an open source
    DC/OS or DC/OS Enterprise repository.

    By default the ``DCOS_CHECKOUT_DIR`` argument is set to the value of the
    ``DCOS_CHECKOUT_DIR`` environment variable.

    If no ``DCOS_CHECKOUT_DIR`` is given, the current working directory is
    used.
    """
    set_logging(verbosity_level=verbose)
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(aws_region=aws_region),
    )
    cluster_instances = ClusterInstances(
        cluster_id=cluster_id,
        aws_region=aws_region,
    )
    cluster = cluster_instances.cluster
    sync_code_to_masters(
        cluster=cluster,
        dcos_checkout_dir=Path(dcos_checkout_dir),
    )
