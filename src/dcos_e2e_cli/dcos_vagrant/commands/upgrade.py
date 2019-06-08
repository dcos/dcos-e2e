"""
Tools for upgrading a DC/OS cluster.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import click

from dcos_e2e.backends import Vagrant
from dcos_e2e.node import Output, Transport
from dcos_e2e_cli.common.arguments import installer_argument
from dcos_e2e_cli.common.create import get_config
from dcos_e2e_cli.common.doctor import get_doctor_message
from dcos_e2e_cli.common.install import run_post_install_steps
from dcos_e2e_cli.common.options import (
    existing_cluster_id_option,
    extra_config_option,
    license_key_option,
    security_mode_option,
    variant_option,
    verbosity_option,
)
from dcos_e2e_cli.common.utils import check_cluster_id_exists, command_path
from dcos_e2e_cli.common.variants import get_install_variant
from dcos_e2e_cli.common.workspaces import workspace_dir_option

from ._common import ClusterVMs, existing_cluster_ids
from ._wait_for_dcos import wait_for_dcos_option
from .doctor import doctor
from .wait import wait


@click.command('upgrade')
@existing_cluster_id_option
@verbosity_option
@extra_config_option
@variant_option
@installer_argument
@workspace_dir_option
@security_mode_option
@wait_for_dcos_option
@license_key_option
@click.pass_context
def upgrade(
    ctx: click.core.Context,
    cluster_id: str,
    extra_config: Dict[str, Any],
    security_mode: Optional[str],
    license_key: Optional[Path],
    variant: str,
    workspace_dir: Path,
    installer: Path,
    wait_for_dcos: bool,
) -> None:
    """
    Upgrade a cluster to a given version of DC/OS.
    """
    doctor_command_name = command_path(sibling_ctx=ctx, command=doctor)
    doctor_message = get_doctor_message(
        doctor_command_name=doctor_command_name,
    )
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    cluster_vms = ClusterVMs(cluster_id=cluster_id)
    cluster_backend = Vagrant()
    cluster = cluster_vms.cluster
    dcos_variant = get_install_variant(
        given_variant=variant,
        installer_path=installer,
        workspace_dir=workspace_dir,
        doctor_message=doctor_message,
    )
    dcos_config = get_config(
        cluster_representation=cluster_vms,
        extra_config=extra_config,
        dcos_variant=dcos_variant,
        security_mode=security_mode,
        license_key=license_key,
    )

    cluster.upgrade_dcos_from_path(
        dcos_installer=installer,
        dcos_config=dcos_config,
        ip_detect_path=cluster_backend.ip_detect_path,
        output=Output.LOG_AND_CAPTURE,
    )

    wait_command_name = command_path(sibling_ctx=ctx, command=wait)
    run_post_install_steps(
        cluster=cluster,
        cluster_id=cluster_id,
        dcos_config=dcos_config,
        doctor_command_name=doctor_command_name,
        http_checks=True,
        wait_command_name=wait_command_name,
        wait_for_dcos=wait_for_dcos,
    )
