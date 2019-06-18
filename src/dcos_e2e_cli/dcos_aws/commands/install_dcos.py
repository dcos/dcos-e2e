"""
Tools for installing DC/OS on a provisioned AWS cluster.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click

from dcos_e2e.backends import AWS
from dcos_e2e_cli.common.arguments import installer_url_argument
from dcos_e2e_cli.common.create import get_config
from dcos_e2e_cli.common.doctor import get_doctor_message
from dcos_e2e_cli.common.install import (
    cluster_install_dcos_from_url,
    run_post_install_steps,
)
from dcos_e2e_cli.common.options import (
    cluster_id_option,
    enable_spinner_option,
    extra_config_option,
    license_key_option,
    security_mode_option,
    verbosity_option,
)
from dcos_e2e_cli.common.options.genconf_dir import genconf_dir_option
from dcos_e2e_cli.common.utils import check_cluster_id_exists, command_path
from dcos_e2e_cli.common.variants import get_install_variant
from dcos_e2e_cli.common.workspaces import workspace_dir_option

from ._common import ClusterInstances, existing_cluster_ids
from ._options import aws_region_option
from ._variant import variant_option
from ._wait_for_dcos import wait_for_dcos_option
from .doctor import doctor
from .wait import wait


@click.command('install')
@installer_url_argument
@variant_option
@wait_for_dcos_option
@extra_config_option
@aws_region_option
@workspace_dir_option
@license_key_option
@genconf_dir_option
@security_mode_option
@verbosity_option
@cluster_id_option
@enable_spinner_option
@click.pass_context
def install_dcos(
    ctx: click.core.Context,
    installer_url: str,
    extra_config: Dict[str, Any],
    variant: str,
    workspace_dir: Path,
    license_key: Optional[Path],
    security_mode: Optional[str],
    aws_region: str,
    cluster_id: str,
    files_to_copy_to_genconf_dir: List[Tuple[Path, Path]],
    wait_for_dcos: bool,
    enable_spinner: bool,
) -> None:
    """
    Install DC/OS on a provisioned AWS cluster.
    """
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(aws_region=aws_region),
    )

    cluster_instances = ClusterInstances(
        cluster_id=cluster_id,
        aws_region=aws_region,
    )

    doctor_command_name = command_path(sibling_ctx=ctx, command=doctor)
    wait_command_name = command_path(sibling_ctx=ctx, command=wait)
    doctor_message = get_doctor_message(
        doctor_command_name=doctor_command_name,
    )
    dcos_variant = get_install_variant(
        given_variant=variant,
        installer_path=None,
        workspace_dir=workspace_dir,
        doctor_message=doctor_message,
        enable_spinner=enable_spinner,
    )

    dcos_config = get_config(
        cluster_representation=cluster_instances,
        extra_config=extra_config,
        dcos_variant=dcos_variant,
        security_mode=security_mode,
        license_key=license_key,
    )

    cluster_backend = AWS()
    cluster = cluster_instances.cluster
    cluster_install_dcos_from_url(
        cluster=cluster,
        cluster_representation=cluster_instances,
        dcos_config=dcos_config,
        dcos_installer=installer_url,
        doctor_message=doctor_message,
        files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
        ip_detect_path=cluster_backend.ip_detect_path,
        enable_spinner=enable_spinner,
    )

    run_post_install_steps(
        cluster=cluster,
        cluster_id=cluster_id,
        dcos_config=dcos_config,
        doctor_command_name=doctor_command_name,
        http_checks=True,
        wait_command_name=wait_command_name,
        wait_for_dcos=wait_for_dcos,
        enable_spinner=enable_spinner,
    )
