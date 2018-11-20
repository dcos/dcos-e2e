"""
Tools for syncing code to a cluster.
"""

from pathlib import Path

import click

from dcos_e2e_cli._vendor.dcos_installer_tools import DCOSVariant
from dcos_e2e_cli.common.arguments import dcos_checkout_dir_argument
from dcos_e2e_cli.common.options import (
    existing_cluster_id_option,
    verbosity_option,
)
from dcos_e2e_cli.common.sync import sync_code_to_masters
from dcos_e2e_cli.common.utils import check_cluster_id_exists, set_logging

from ._common import ClusterVMs, existing_cluster_ids


@click.command('sync')
@existing_cluster_id_option
@dcos_checkout_dir_argument
@verbosity_option
def sync_code(
    cluster_id: str,
    dcos_checkout_dir: str,
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
        existing_cluster_ids=existing_cluster_ids(),
    )
    cluster_vms = ClusterVMs(cluster_id=cluster_id)
    cluster = cluster_vms.cluster
    dcos_variant = {
        True: DCOSVariant.ENTERPRISE,
        False: DCOSVariant.OSS,
    }[cluster_vms.is_enterprise]
    sync_code_to_masters(
        cluster=cluster,
        dcos_checkout_dir=Path(dcos_checkout_dir),
        dcos_variant=dcos_variant,
    )
