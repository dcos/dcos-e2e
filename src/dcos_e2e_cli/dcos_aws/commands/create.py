"""
Tools for creating a DC/OS cluster.
"""

import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import boto3
import click

from dcos_e2e.backends import AWS
from dcos_e2e.distributions import Distribution
from dcos_e2e_cli.common.arguments import installer_url_argument
from dcos_e2e_cli.common.create import CREATE_HELP, create_cluster, get_config
from dcos_e2e_cli.common.doctor import get_doctor_message
from dcos_e2e_cli.common.install import (
    cluster_install_dcos_from_url,
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
    verbosity_option,
)
from dcos_e2e_cli.common.options.cluster_size import (
    agents_option,
    masters_option,
    public_agents_option,
)
from dcos_e2e_cli.common.options.genconf_dir import genconf_dir_option
from dcos_e2e_cli.common.utils import (
    check_cluster_id_unique,
    command_path,
    write_key_pair,
)
from dcos_e2e_cli.common.variants import get_install_variant
from dcos_e2e_cli.common.workspaces import workspace_dir_option

from ._common import (
    CLUSTER_ID_TAG_KEY,
    KEY_NAME_TAG_KEY,
    LINUX_DISTRIBUTIONS,
    NODE_TYPE_AGENT_TAG_VALUE,
    NODE_TYPE_MASTER_TAG_VALUE,
    NODE_TYPE_PUBLIC_AGENT_TAG_VALUE,
    NODE_TYPE_TAG_KEY,
    SSH_USER_TAG_KEY,
    WORKSPACE_DIR_TAG_KEY,
    ClusterInstances,
    existing_cluster_ids,
)
from ._custom_tag import custom_tag_option
from ._options import (
    aws_instance_type_option,
    aws_region_option,
    linux_distribution_option,
)
from ._variant import variant_option
from ._wait_for_dcos import wait_for_dcos_option
from .doctor import doctor
from .wait import wait


@click.command('create', help=CREATE_HELP)
@installer_url_argument
@custom_tag_option
@variant_option
@wait_for_dcos_option
@masters_option
@agents_option
@extra_config_option
@public_agents_option
@aws_instance_type_option
@aws_region_option
@linux_distribution_option
@workspace_dir_option
@license_key_option
@genconf_dir_option
@security_mode_option
@copy_to_master_option
@verbosity_option
@cluster_id_option
@enable_selinux_enforcing_option
@enable_spinner_option
@click.pass_context
def create(
    ctx: click.core.Context,
    agents: int,
    installer_url: str,
    extra_config: Dict[str, Any],
    masters: int,
    public_agents: int,
    variant: str,
    workspace_dir: Path,
    license_key: Optional[Path],
    security_mode: Optional[str],
    copy_to_master: List[Tuple[Path, Path]],
    aws_instance_type: str,
    aws_region: str,
    linux_distribution: str,
    cluster_id: str,
    enable_selinux_enforcing: bool,
    files_to_copy_to_genconf_dir: List[Tuple[Path, Path]],
    custom_tag: Dict[str, str],
    wait_for_dcos: bool,
    enable_spinner: bool,
) -> None:
    """
    Create a DC/OS cluster.
    """
    check_cluster_id_unique(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(aws_region=aws_region),
    )
    ssh_keypair_dir = workspace_dir / 'ssh'
    ssh_keypair_dir.mkdir(parents=True)
    key_name = 'key-{random}'.format(random=uuid.uuid4().hex)
    public_key_path = ssh_keypair_dir / 'id_rsa.pub'
    private_key_path = ssh_keypair_dir / 'id_rsa'
    write_key_pair(
        public_key_path=public_key_path,
        private_key_path=private_key_path,
    )

    ec2 = boto3.resource('ec2', region_name=aws_region)
    ec2.import_key_pair(
        KeyName=key_name,
        PublicKeyMaterial=public_key_path.read_bytes(),
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
    ssh_user = {
        Distribution.CENTOS_7: 'centos',
        Distribution.UBUNTU_16_04: 'ubuntu',
        Distribution.RHEL_7: 'ec2-user',
    }

    distribution = LINUX_DISTRIBUTIONS[linux_distribution]

    default_user = ssh_user[distribution]

    cluster_tags = {
        SSH_USER_TAG_KEY: default_user,
        CLUSTER_ID_TAG_KEY: cluster_id,
        WORKSPACE_DIR_TAG_KEY: str(workspace_dir),
        KEY_NAME_TAG_KEY: key_name,
        **custom_tag,
    }

    master_tags = {NODE_TYPE_TAG_KEY: NODE_TYPE_MASTER_TAG_VALUE}
    agent_tags = {NODE_TYPE_TAG_KEY: NODE_TYPE_AGENT_TAG_VALUE}
    public_agent_tags = {NODE_TYPE_TAG_KEY: NODE_TYPE_PUBLIC_AGENT_TAG_VALUE}
    cluster_backend = AWS(
        aws_key_pair=(key_name, private_key_path),
        workspace_dir=workspace_dir,
        aws_instance_type=aws_instance_type,
        aws_region=aws_region,
        linux_distribution=distribution,
        ec2_instance_tags=cluster_tags,
        master_ec2_instance_tags=master_tags,
        agent_ec2_instance_tags=agent_tags,
        public_agent_ec2_instance_tags=public_agent_tags,
        aws_cloudformation_stack_name=cluster_id,
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
                sudo=True,
            )

    cluster_instances = ClusterInstances(
        cluster_id=cluster_id,
        aws_region=aws_region,
    )

    dcos_config = get_config(
        cluster_representation=cluster_instances,
        extra_config=extra_config,
        dcos_variant=dcos_variant,
        security_mode=security_mode,
        license_key=license_key,
    )

    cluster_install_dcos_from_url(
        cluster=cluster,
        cluster_representation=cluster_instances,
        dcos_config=dcos_config,
        dcos_installer=installer_url,
        doctor_message=doctor_message,
        enable_spinner=enable_spinner,
        files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
        ip_detect_path=cluster_backend.ip_detect_path,
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
