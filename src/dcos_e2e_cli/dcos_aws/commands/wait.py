"""
Tools for waiting for a cluster.
"""

import click

from dcos_e2e_cli.common.options import (
    existing_cluster_id_option,
    superuser_password_option,
    superuser_username_option,
    verbosity_option,
)
from dcos_e2e_cli.common.utils import check_cluster_id_exists, set_logging
from dcos_e2e_cli.common.wait import wait_for_dcos

from ._common import ClusterInstances, existing_cluster_ids
from ._options import aws_region_option
from .doctor import doctor


@click.command('wait')
@existing_cluster_id_option
@superuser_username_option
@superuser_password_option
@verbosity_option
@aws_region_option
@click.pass_context
def wait(
    ctx: click.core.Context,
    cluster_id: str,
    superuser_username: str,
    superuser_password: str,
    verbose: int,
    aws_region: str,
) -> None:
    """
    Wait for DC/OS to start.
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
    wait_for_dcos(
        dcos_variant=cluster_instances.dcos_variant,
        cluster=cluster_instances.cluster,
        superuser_username=superuser_username,
        superuser_password=superuser_password,
        http_checks=True,
        doctor_command=doctor,
        sibling_ctx=ctx,
    )
