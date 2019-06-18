"""
Tools for creating a DC/OS cluster.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click

from dcos_e2e.backends import Vagrant
from dcos_e2e_cli.common.arguments import installer_path_argument
from dcos_e2e_cli.common.create import CREATE_HELP, create_cluster, get_config
from dcos_e2e_cli.common.doctor import get_doctor_message
from dcos_e2e_cli.common.install import (
    cluster_install_dcos_from_path,
    run_post_install_steps,
)
from dcos_e2e_cli.common.options import (
    cluster_id_option,
    copy_to_master_option,
    enable_selinux_enforcing_option,
    enable_spinner_option,
    extra_config_option,
    license_key_option,
    security_mode_option,
    variant_option,
    verbosity_option,
)
from dcos_e2e_cli.common.options.cluster_size import (
    agents_option,
    masters_option,
    public_agents_option,
)
from dcos_e2e_cli.common.options.genconf_dir import genconf_dir_option
from dcos_e2e_cli.common.utils import check_cluster_id_unique, command_path
from dcos_e2e_cli.common.variants import get_install_variant
from dcos_e2e_cli.common.workspaces import workspace_dir_option

from ._common import (
    CLUSTER_ID_DESCRIPTION_KEY,
    WORKSPACE_DIR_DESCRIPTION_KEY,
    ClusterVMs,
    existing_cluster_ids,
)
from ._options import (
    vagrant_box_url_option,
    vagrant_box_version_option,
    vm_memory_mb_option,
)
from ._wait_for_dcos import wait_for_dcos_option
from .doctor import doctor
from .wait import wait


@click.command('create', help=CREATE_HELP)
@installer_path_argument
@masters_option
@agents_option
@extra_config_option
@public_agents_option
@workspace_dir_option
@variant_option
@license_key_option
@genconf_dir_option
@security_mode_option
@copy_to_master_option
@cluster_id_option
@verbosity_option
@vm_memory_mb_option
@enable_selinux_enforcing_option
@enable_spinner_option
@vagrant_box_url_option
@vagrant_box_version_option
@wait_for_dcos_option
@click.pass_context
def create(
    ctx: click.core.Context,
    agents: int,
    installer: Path,
    extra_config: Dict[str, Any],
    masters: int,
    public_agents: int,
    variant: str,
    workspace_dir: Path,
    license_key: Optional[Path],
    security_mode: Optional[str],
    copy_to_master: List[Tuple[Path, Path]],
    cluster_id: str,
    enable_selinux_enforcing: bool,
    files_to_copy_to_genconf_dir: List[Tuple[Path, Path]],
    wait_for_dcos: bool,
    vm_memory_mb: int,
    enable_spinner: bool,
    vagrant_box_url: str,
    vagrant_box_version: str,
) -> None:
    """
    Create a DC/OS cluster.
    """
    check_cluster_id_unique(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )

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

    description = {
        CLUSTER_ID_DESCRIPTION_KEY: cluster_id,
        WORKSPACE_DIR_DESCRIPTION_KEY: str(workspace_dir),
    }
    cluster_backend = Vagrant(
        workspace_dir=workspace_dir,
        virtualbox_description=json.dumps(obj=description),
        vm_memory_mb=vm_memory_mb,
        vagrant_box_url=vagrant_box_url,
        vagrant_box_version=vagrant_box_version,
    )

    cluster = create_cluster(
        cluster_backend=cluster_backend,
        masters=masters,
        agents=agents,
        public_agents=public_agents,
        doctor_message=doctor_message,
        enable_spinner=enable_spinner,
    )

    nodes = {*cluster.masters, *cluster.agents, *cluster.public_agents}
    for node in nodes:
        if enable_selinux_enforcing:
            node.run(args=['setenforce', '1'], sudo=True)

    for node in cluster.masters:
        for path_pair in copy_to_master:
            local_path, remote_path = path_pair
            node.send_file(
                local_path=local_path,
                remote_path=remote_path,
            )

    cluster_vms = ClusterVMs(cluster_id=cluster_id)
    dcos_config = get_config(
        cluster_representation=cluster_vms,
        extra_config=extra_config,
        dcos_variant=dcos_variant,
        security_mode=security_mode,
        license_key=license_key,
    )

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
