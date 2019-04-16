"""
Tools for opening a cluster's web UI.
"""

import click

from dcos_e2e_cli.common.options import (
    existing_cluster_id_option,
    verbosity_option,
)
from dcos_e2e_cli.common.utils import check_cluster_id_exists
from dcos_e2e_cli.common.web import launch_web_ui

from ._common import ClusterVMs, existing_cluster_ids


@click.command('web')
@existing_cluster_id_option
@verbosity_option
def web(cluster_id: str) -> None:
    """
    Open the browser at the web UI.

    Note that the web UI may not be available at first.
    Consider using ``minidcos vagrant wait`` before running this command.
    """
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    cluster_vms = ClusterVMs(cluster_id=cluster_id)
    launch_web_ui(cluster=cluster_vms.cluster)
