from pathlib import Path
from typing import Any, Dict, Optional

import click

from dcos_e2e.backends import Docker
from dcos_e2e.node import Output, Role, Transport
from dcos_e2e_cli.common.arguments import installer_argument
from dcos_e2e_cli.common.create import get_config
from dcos_e2e_cli.common.doctor import get_doctor_message
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

from ._common import ClusterContainers, existing_cluster_ids
from ._options import node_transport_option
from .doctor import doctor


@click.command('upgrade')
@existing_cluster_id_option
@verbosity_option
@extra_config_option
@variant_option
@node_transport_option
@installer_argument
@workspace_dir_option
@security_mode_option
@license_key_option
@click.pass_context
def upgrade(
    ctx: click.core.Context,
    cluster_id: str,
    transport: Transport,
    extra_config: Dict[str, Any],
    security_mode: Optional[str],
    license_key: Optional[Path],
    variant: str,
    workspace_dir: Path,
    installer: Path,
) -> None:
    """
    XXX
    """
    doctor_command_name = command_path(sibling_ctx=ctx, command=doctor)
    doctor_message = get_doctor_message(
        doctor_command_name=doctor_command_name,
    )
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        transport=transport,
    )
    cluster_backend = Docker()
    cluster = cluster_containers.cluster
    dcos_variant = get_install_variant(
        given_variant=variant,
        installer_path=installer,
        workspace_dir=workspace_dir,
        doctor_message=doctor_message,
    )
    dcos_config = get_config(
        cluster_representation=cluster_containers,
        extra_config=extra_config,
        dcos_variant=dcos_variant,
        security_mode=security_mode,
        license_key=license_key,
    )
    for nodes, role in (
        (cluster.masters, Role.MASTER),
        (cluster.agents, Role.AGENT),
        (cluster.public_agents, Role.PUBLIC_AGENT),
    ):
        for node in nodes:
            node.upgrade_dcos_from_path(
                dcos_installer=installer,
                dcos_config=dcos_config,
                ip_detect_path=cluster_backend.ip_detect_path,
                role=role,
                output=Output.LOG_AND_CAPTURE,
            )
    # TODO print wait message
