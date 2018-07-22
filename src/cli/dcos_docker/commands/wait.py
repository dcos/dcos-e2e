"""
Tools for waiting for a cluster.
"""

import click
import click_spinner
import urllib3

from cli.common.options import (
    superuser_password_option,
    superuser_username_option,
    verbosity_option,
)
from cli.common.utils import set_logging
from dcos_e2e.node import Transport

from ._common import ClusterContainers
from ._options import existing_cluster_id_option, node_transport_option


@click.command('wait')
@existing_cluster_id_option
@superuser_username_option
@superuser_password_option
@click.option(
    '--skip-http-checks',
    is_flag=True,
    help=(
        'Do not wait for checks which require an HTTP connection to the '
        'cluster. '
        'If this flag is used, this command may return before DC/OS is fully '
        'ready. '
        'Use this flag in cases where an HTTP connection cannot be made to '
        'the cluster. '
        'For example this is useful on macOS without a VPN set up.'
    ),
)
@node_transport_option
@verbosity_option
def wait(
    cluster_id: str,
    superuser_username: str,
    superuser_password: str,
    transport: Transport,
    skip_http_checks: bool,
    verbose: int,
) -> None:
    """
    Wait for DC/OS to start.
    """
    set_logging(verbosity_level=verbose)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    message = (
        'A cluster may take some time to be ready.\n'
        'The amount of time it takes to start a cluster depends on a variety '
        'of factors.\n'
        'If you are concerned that this is hanging, try "dcos-docker doctor" '
        'to diagnose common issues.'
    )
    click.echo(message)
    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        transport=transport,
    )
    http_checks = not skip_http_checks
    with click_spinner.spinner():
        if cluster_containers.is_enterprise:
            cluster_containers.cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
                http_checks=http_checks,
            )
            return

        cluster_containers.cluster.wait_for_dcos_oss(http_checks=http_checks)
