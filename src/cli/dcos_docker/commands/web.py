"""
Tools for opening a cluster's web UI.
"""

import click

from cli.common.options import existing_cluster_id_option, verbosity_option
from cli.common.utils import check_cluster_id_exists, set_logging
from dcos_e2e.node import Transport

from ._common import ClusterContainers, existing_cluster_ids


@click.command('web')
@existing_cluster_id_option
@verbosity_option
def web(cluster_id: str, verbose: int) -> None:
    """
    Open the browser at the web UI.

    Note that the web UI may not be available at first.
    Consider using ``dcos-docker wait`` before running this command.
    """
    set_logging(verbosity_level=verbose)
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        # The transport is not used so does not matter.
        transport=Transport.DOCKER_EXEC,
    )
    cluster = cluster_containers.cluster
    master = next(iter(cluster.masters))
    web_ui = 'http://' + str(master.public_ip_address)
    click.launch(web_ui)
