"""
Provisioning an AWS cluster to install DC/OS.
"""

import uuid
from pathlib import Path
from typing import Dict, List, Tuple

import boto3
import click

from dcos_e2e.backends import AWS
from dcos_e2e.distributions import Distribution
from dcos_e2e_cli.common.create import create_cluster
from dcos_e2e_cli.common.doctor import get_doctor_message
from dcos_e2e_cli.common.options import (
    cluster_id_option,
    copy_to_master_option,
    enable_selinux_enforcing_option,
    enable_spinner_option,
    verbosity_option,
)
from dcos_e2e_cli.common.options.cluster_size import (
    agents_option,
    masters_option,
    public_agents_option,
)
from dcos_e2e_cli.common.utils import (
    check_cluster_id_unique,
    command_path,
    write_key_pair,
)
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
    existing_cluster_ids,
)
from ._custom_tag import custom_tag_option
from ._options import (
    aws_instance_type_option,
    aws_region_option,
    linux_distribution_option,
)
from .doctor import doctor


@click.command('provision')
@custom_tag_option
@masters_option
@agents_option
@public_agents_option
@aws_instance_type_option
@aws_region_option
@linux_distribution_option
@workspace_dir_option
@copy_to_master_option
@verbosity_option
@cluster_id_option
@enable_selinux_enforcing_option
@enable_spinner_option
@click.pass_context
def provision(
    ctx: click.core.Context,
    agents: int,
    masters: int,
    public_agents: int,
    workspace_dir: Path,
    copy_to_master: List[Tuple[Path, Path]],
    aws_instance_type: str,
    aws_region: str,
    linux_distribution: str,
    cluster_id: str,
    enable_selinux_enforcing: bool,
    custom_tag: Dict[str, str],
    enable_spinner: bool,
) -> None:
    """
    Provision an AWS cluster to install DC/OS.
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
    doctor_message = get_doctor_message(
        doctor_command_name=doctor_command_name,
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
