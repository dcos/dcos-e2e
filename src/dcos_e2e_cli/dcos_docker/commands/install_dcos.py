"""
Installing DC/OS on a Docker cluster.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click

from dcos_e2e.backends import Docker
from dcos_e2e.node import Transport
from dcos_e2e_cli.common.arguments import installer_path_argument
from dcos_e2e_cli.common.create import get_config
from dcos_e2e_cli.common.doctor import get_doctor_message
from dcos_e2e_cli.common.install import (
    cluster_install_dcos_from_path,
    run_post_install_steps,
)
from dcos_e2e_cli.common.options import (
    enable_spinner_option,
    existing_cluster_id_option,
    extra_config_option,
    license_key_option,
    security_mode_option,
    variant_option,
    verbosity_option,
)
from dcos_e2e_cli.common.options.genconf_dir import genconf_dir_option
from dcos_e2e_cli.common.utils import check_cluster_id_exists, command_path
from dcos_e2e_cli.common.variants import get_install_variant
from dcos_e2e_cli.common.workspaces import workspace_dir_option

from ._common import ClusterContainers, existing_cluster_ids
from ._options import node_transport_option, wait_for_dcos_option
from .doctor import doctor
from .wait import wait


@click.command('install')
@genconf_dir_option
@installer_path_argument
@existing_cluster_id_option
@extra_config_option
@security_mode_option
@license_key_option
@node_transport_option
@variant_option
@verbosity_option
@wait_for_dcos_option
@workspace_dir_option
@enable_spinner_option
@click.pass_context
def install_dcos(
    ctx: click.core.Context,
    cluster_id: str,
    files_to_copy_to_genconf_dir: List[Tuple[Path, Path]],
    installer: Path,
    license_key: Optional[Path],
    extra_config: Dict[str, Any],
    security_mode: Optional[str],
    variant: str,
    workspace_dir: Path,
    transport: Transport,
    wait_for_dcos: bool,
    enable_spinner: bool,
) -> None:
    """
    Install DC/OS on the given Docker cluster.
    """
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        transport=transport,
    )
    cluster = cluster_containers.cluster

    doctor_command_name = command_path(sibling_ctx=ctx, command=doctor)
    doctor_message = get_doctor_message(
        doctor_command_name=doctor_command_name,
    )
    http_checks = bool(transport == Transport.SSH)
    wait_command_name = command_path(sibling_ctx=ctx, command=wait)

    cluster_backend = Docker()
    ip_detect_path = cluster_backend.ip_detect_path

    dcos_variant = get_install_variant(
        given_variant=variant,
        installer_path=installer,
        workspace_dir=workspace_dir,
        doctor_message=doctor_message,
        enable_spinner=enable_spinner,
    )

    dcos_config = get_config(
        cluster_representation=cluster_containers,
        extra_config=extra_config,
        dcos_variant=dcos_variant,
        security_mode=security_mode,
        license_key=license_key,
    )

    cluster_install_dcos_from_path(
        cluster=cluster,
        cluster_representation=cluster_containers,
        dcos_config=dcos_config,
        ip_detect_path=ip_detect_path,
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
        http_checks=http_checks,
        wait_command_name=wait_command_name,
        wait_for_dcos=wait_for_dcos,
        enable_spinner=enable_spinner,
    )
