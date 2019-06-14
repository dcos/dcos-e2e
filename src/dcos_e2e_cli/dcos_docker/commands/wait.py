"""
Tools for waiting for a cluster.
"""

import click

from dcos_e2e.node import Transport
from dcos_e2e_cli.common.options import (
    enable_spinner_option,
    existing_cluster_id_option,
    superuser_password_option,
    superuser_username_option,
    verbosity_option,
)
from dcos_e2e_cli.common.utils import check_cluster_id_exists, command_path
from dcos_e2e_cli.common.wait import wait_for_dcos

from ._common import ClusterContainers, existing_cluster_ids
from ._options import node_transport_option
from .doctor import doctor


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
    show_default=True,
)
@node_transport_option
@verbosity_option
@enable_spinner_option
@click.pass_context
def wait(
    ctx: click.core.Context,
    cluster_id: str,
    superuser_username: str,
    superuser_password: str,
    transport: Transport,
    skip_http_checks: bool,
    enable_spinner: bool,
) -> None:
    """
    Wait for DC/OS to start.
    """
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        transport=transport,
    )

    http_checks = not skip_http_checks
    doctor_command_name = command_path(sibling_ctx=ctx, command=doctor)

    wait_for_dcos(
        cluster=cluster_containers.cluster,
        superuser_username=superuser_username,
        superuser_password=superuser_password,
        http_checks=http_checks,
        doctor_command_name=doctor_command_name,
        enable_spinner=enable_spinner,
    )
