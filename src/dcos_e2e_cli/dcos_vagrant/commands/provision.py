"""
Tools for provisioning a Vagrant cluster to install DC/OS.
"""

import json
from pathlib import Path

import click

from dcos_e2e.backends import Vagrant
from dcos_e2e_cli.common.create import create_cluster
from dcos_e2e_cli.common.doctor import get_doctor_message
from dcos_e2e_cli.common.options import (
    cluster_id_option,
    enable_selinux_enforcing_option,
    enable_spinner_option,
    verbosity_option,
)
from dcos_e2e_cli.common.options.cluster_size import (
    agents_option,
    masters_option,
    public_agents_option,
)
from dcos_e2e_cli.common.utils import check_cluster_id_unique, command_path
from dcos_e2e_cli.common.workspaces import workspace_dir_option

from ._common import (
    CLUSTER_ID_DESCRIPTION_KEY,
    WORKSPACE_DIR_DESCRIPTION_KEY,
    existing_cluster_ids,
)
from ._options import (
    vagrant_box_url_option,
    vagrant_box_version_option,
    vm_memory_mb_option,
)
from .doctor import doctor


@click.command('provision')
@masters_option
@agents_option
@public_agents_option
@workspace_dir_option
@cluster_id_option
@verbosity_option
@enable_selinux_enforcing_option
@enable_spinner_option
@vagrant_box_url_option
@vagrant_box_version_option
@vm_memory_mb_option
@click.pass_context
def provision(
    ctx: click.core.Context,
    agents: int,
    masters: int,
    public_agents: int,
    workspace_dir: Path,
    cluster_id: str,
    enable_selinux_enforcing: bool,
    vm_memory_mb: int,
    enable_spinner: bool,
    vagrant_box_url: str,
    vagrant_box_version: str,
) -> None:
    """
    Provision a Vagrant cluster for installing DC/OS.
    """
    check_cluster_id_unique(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )

    doctor_command_name = command_path(sibling_ctx=ctx, command=doctor)
    doctor_message = get_doctor_message(
        doctor_command_name=doctor_command_name,
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
