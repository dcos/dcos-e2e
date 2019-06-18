"""
Install DC/OS on a provisioned Vagrant cluster.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click

from dcos_e2e.backends import Vagrant
from dcos_e2e_cli.common.arguments import installer_path_argument
from dcos_e2e_cli.common.create import get_config
from dcos_e2e_cli.common.doctor import get_doctor_message
from dcos_e2e_cli.common.install import (
    cluster_install_dcos_from_path,
    run_post_install_steps,
)
from dcos_e2e_cli.common.options import (
    cluster_id_option,
    enable_spinner_option,
    extra_config_option,
    license_key_option,
    security_mode_option,
    variant_option,
    verbosity_option,
)
from dcos_e2e_cli.common.options.genconf_dir import genconf_dir_option
from dcos_e2e_cli.common.utils import command_path
from dcos_e2e_cli.common.variants import get_install_variant
from dcos_e2e_cli.common.workspaces import workspace_dir_option

from ._common import ClusterVMs
from ._wait_for_dcos import wait_for_dcos_option
from .doctor import doctor
from .wait import wait


@click.command('install')
@installer_path_argument
@extra_config_option
@workspace_dir_option
@variant_option
@license_key_option
@genconf_dir_option
@security_mode_option
@cluster_id_option
@verbosity_option
@enable_spinner_option
@wait_for_dcos_option
@click.pass_context
def install_dcos(
    ctx: click.core.Context,
    installer: Path,
    extra_config: Dict[str, Any],
    variant: str,
    workspace_dir: Path,
    license_key: Optional[Path],
    security_mode: Optional[str],
    cluster_id: str,
    files_to_copy_to_genconf_dir: List[Tuple[Path, Path]],
    wait_for_dcos: bool,
    enable_spinner: bool,
) -> None:
    """
    Install DC/OS on a provisioned Vagrant cluster.
    """
    doctor_command_name = command_path(sibling_ctx=ctx, command=doctor)
    wait_command_name = command_path(sibling_ctx=ctx, command=wait)
    doctor_message = get_doctor_message(
        doctor_command_name=doctor_command_name,
    )

    dcos_variant = get_install_variant(
        given_variant=variant,
        installer_path=installer,
        workspace_dir=workspace_dir,
        doctor_message=doctor_message,
        enable_spinner=enable_spinner,
    )

    cluster_backend = Vagrant()

    cluster_vms = ClusterVMs(cluster_id=cluster_id)
    dcos_config = get_config(
        cluster_representation=cluster_vms,
        extra_config=extra_config,
        dcos_variant=dcos_variant,
        security_mode=security_mode,
        license_key=license_key,
    )

    cluster = cluster_vms.cluster

    cluster_install_dcos_from_path(
        cluster=cluster,
        cluster_representation=cluster_vms,
        dcos_config=dcos_config,
        ip_detect_path=cluster_backend.ip_detect_path,
        doctor_message=doctor_message,
        dcos_installer=installer,
        files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
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
