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

from ._common import ClusterVMs, existing_cluster_ids


@click.command('wait')
@existing_cluster_id_option
@superuser_username_option
@superuser_password_option
@verbosity_option
def wait(
    cluster_id: str,
    superuser_username: str,
    superuser_password: str,
    verbose: int,
) -> None:
    """
    Wait for DC/OS to start.
    """
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    set_logging(verbosity_level=verbose)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    message = (
        'A cluster may take some time to be ready.\n'
        'The amount of time it takes to start a cluster depends on a variety '
        'of factors.\n'
        'If you are concerned that this is hanging, try "dcos-vagrant doctor" '
        'to diagnose common issues.'
    )
    click.echo(message)
    cluster_vms = ClusterVMs(cluster_id=cluster_id)
    with click_spinner.spinner():
        if cluster_vms.is_enterprise:
            cluster_vms.cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
                http_checks=True,
            )
            return

        cluster_vms.cluster.wait_for_dcos_oss(http_checks=True)
