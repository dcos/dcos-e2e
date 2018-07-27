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
from cli.common.utils import (
    check_cluster_id_exists,
    set_logging,
    show_wait_help,
)

from ._common import ClusterVMs, existing_cluster_ids
from .doctor import doctor


@click.command('wait')
@existing_cluster_id_option
@superuser_username_option
@superuser_password_option
@verbosity_option
@click.pass_context
def wait(
    ctx: click.core.Context,
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
    cluster_vms = ClusterVMs(cluster_id=cluster_id)
    parent = ctx.parent
    assert parent is not None
    doctor_command_name = '{info_name} {doctor_name}'.format(
        info_name=parent.info_name,
        doctor_name=doctor.name,
    )
    show_wait_help(
        is_enterprise=cluster_vms.is_enterprise,
        doctor_command_name=doctor_command_name,
    )
    with click_spinner.spinner():
        if cluster_vms.is_enterprise:
            cluster_vms.cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
                http_checks=True,
            )
            return

        cluster_vms.cluster.wait_for_dcos_oss(http_checks=True)
