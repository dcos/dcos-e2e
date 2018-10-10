"""
Tools for opening a cluster's web UI.
"""

import click
from cli.common.options import existing_cluster_id_option, verbosity_option
from cli.common.utils import check_cluster_id_exists, set_logging

from ._common import ClusterInstances, existing_cluster_ids
from ._options import aws_region_option


@click.command('web')
@existing_cluster_id_option
@aws_region_option
@verbosity_option
def web(cluster_id: str, aws_region: str, verbose: int) -> None:
    """
    Open the browser at the web UI.

    Note that the web UI may not be available at first.
    Consider using ``dcos-aws wait`` before running this command.
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
    master = next(iter(cluster.masters))
    web_ui = 'http://' + str(master.public_ip_address)
    click.launch(web_ui)
