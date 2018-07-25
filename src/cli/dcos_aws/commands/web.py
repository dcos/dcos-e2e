"""
Tools for opening a cluster's web UI.
"""

import click

from cli.common.options import existing_cluster_id_option
from cli.common.utils import check_cluster_id_exists

from ._common import ClusterVMs, existing_cluster_ids


@click.command('web')
@existing_cluster_id_option
def web(cluster_id: str) -> None:
    """
    Open the browser at the web UI.

    Note that the web UI may not be available at first.
    Consider using ``dcos-vagrant wait`` before running this command.
    """
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    cluster_vms = ClusterVMs(cluster_id=cluster_id)
    cluster = cluster_vms.cluster
    master = next(iter(cluster.masters))
    web_ui = 'http://' + str(master.public_ip_address)
    click.launch(web_ui)
