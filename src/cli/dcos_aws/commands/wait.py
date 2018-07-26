"""
Tools for waiting for a cluster.
"""

import click
import click_spinner
import urllib3

from cli.common.options import (
    existing_cluster_id_option,
    superuser_password_option,
    superuser_username_option,
    verbosity_option,
)
from cli.common.utils import check_cluster_id_exists, set_logging

from ._common import ClusterInstances, existing_cluster_ids
from ._options import aws_region_option


@click.command('wait')
@existing_cluster_id_option
@superuser_username_option
@superuser_password_option
@verbosity_option
@aws_region_option
def wait(
    cluster_id: str,
    superuser_username: str,
    superuser_password: str,
    verbose: int,
    aws_region: str,
) -> None:
    """
    Wait for DC/OS to start.
    """
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(aws_region=aws_region),
    )
    set_logging(verbosity_level=verbose)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    message = (
        'A cluster may take some time to be ready.\n'
        'The amount of time it takes to start a cluster depends on a variety '
        'of factors.\n'
        'If you are concerned that this is hanging, try "dcos-aws doctor" '
        'to diagnose common issues.'
    )
    click.echo(message)
    cluster_instances = ClusterInstances(
        cluster_id=cluster_id,
        aws_region=aws_region,
    )
    with click_spinner.spinner():
        if cluster_instances.is_enterprise:
            cluster_instances.cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
                http_checks=True,
            )
            return

        cluster_instances.cluster.wait_for_dcos_oss(http_checks=True)
