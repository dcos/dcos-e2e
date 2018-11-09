"""
Tools for creating a DC/OS cluster.
"""

import sys
import tempfile
import uuid
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, List, Optional, Tuple, Union

import boto3
import click
import click_spinner
from passlib.hash import sha512_crypt

from dcos_e2e.backends import AWS
from dcos_e2e.cluster import Cluster
from dcos_e2e.distributions import Distribution
from dcos_e2e_cli.common.options import (
    agents_option,
    cluster_id_option,
    copy_to_master_option,
    enable_selinux_enforcing_option,
    extra_config_option,
    genconf_dir_option,
    license_key_option,
    masters_option,
    public_agents_option,
    security_mode_option,
    verbosity_option,
    workspace_dir_option,
)
from dcos_e2e_cli.common.utils import (
    check_cluster_id_unique,
    set_logging,
    write_key_pair,
)

from ._common import (
    CLUSTER_ID_TAG_KEY,
    KEY_NAME_TAG_KEY,
    LINUX_DISTRIBUTIONS,
    NODE_TYPE_AGENT_TAG_VALUE,
    NODE_TYPE_MASTER_TAG_VALUE,
    NODE_TYPE_PUBLIC_AGENT_TAG_VALUE,
    NODE_TYPE_TAG_KEY,
    SSH_USER_TAG_KEY,
    VARIANT_TAG_KEY,
    WORKSPACE_DIR_TAG_KEY,
    existing_cluster_ids,
)
from ._options import aws_region_option, linux_distribution_option


def _validate_tags(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Any,
) -> Dict[str, int]:
    """
    Turn tag strings into a Dict.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    tags = {}  # type: Dict[str, int]
    for tag_definition in value:
        parts = tag_definition.split(':')

        if len(parts) != 2:
            message = (
                '"{tag_definition}" is not a valid tag. '
                'Please follow this syntax: <TAG_KEY>:<TAG_VALUE>.'
            ).format(tag_definition=tag_definition)
            raise click.BadParameter(message=message)

        tag_key, tag_value = parts
        if tag_key in tags:
            message = 'Tag key "{tag_key}" specified multiple times.'.format(
                tag_key=tag_key,
            )
            raise click.BadParameter(message=message)

        tags[tag_key] = tag_value
    return tags


@click.command('create')
@click.argument(
    'artifact_url',
    type=str,
)
@click.option(
    '--custom-tag',
    type=str,
    callback=_validate_tags,
    help='Add tags to EC2 instances in the format "<TAG_KEY>:<TAG_VALUE>".',
    multiple=True,
)
@click.option(
    '--variant',
    type=click.Choice(['oss', 'enterprise']),
    required=True,
    help=(
        'Choose the DC/OS variant. '
        'If the variant does not match the variant of the given artifact URL, '
        'an error will occur. '
    ),
)
@masters_option
@agents_option
@extra_config_option
@public_agents_option
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
def create(
    agents: int,
    artifact_url: str,
    extra_config: Dict[str, Any],
    masters: int,
    public_agents: int,
    variant: str,
    workspace_dir: Optional[Path],
    license_key: Optional[str],
    security_mode: Optional[str],
    copy_to_master: List[Tuple[Path, Path]],
    verbose: int,
    aws_region: str,
    linux_distribution: str,
    cluster_id: str,
    enable_selinux_enforcing: bool,
    genconf_dir: Optional[Path],
    custom_tag: Dict[str, str],
) -> None:
    """
    Create a DC/OS cluster.

        DC/OS Enterprise

            \b
            DC/OS Enterprise clusters require different configuration variables to DC/OS OSS.
            For example, enterprise clusters require the following configuration parameters:

            ``superuser_username``, ``superuser_password_hash``, ``fault_domain_enabled``, ``license_key_contents``

            \b
            These can all be set in ``--extra-config``.
            However, some defaults are provided for all but the license key.

            \b
            The default superuser username is ``admin``.
            The default superuser password is ``admin``.
            The default ``fault_domain_enabled`` is ``false``.

            \b
            ``license_key_contents`` must be set for DC/OS Enterprise 1.11 and above.
            This is set to one of the following, in order:

            \b
            * The ``license_key_contents`` set in ``--extra-config``.
            * The contents of the path given with ``--license-key``.
            * The contents of the path set in the ``DCOS_LICENSE_KEY_PATH`` environment variable.

            \b
            If none of these are set, ``license_key_contents`` is not given.
    """  # noqa: E501
    set_logging(verbosity_level=verbose)
    check_cluster_id_unique(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(aws_region=aws_region),
    )
    base_workspace_dir = workspace_dir or Path(tempfile.gettempdir())
    workspace_dir = base_workspace_dir / uuid.uuid4().hex
    workspace_dir.mkdir(parents=True)
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

    doctor_message = 'Try `minidcos aws doctor` for troubleshooting help.'
    enterprise = bool(variant == 'enterprise')

    ssh_user = {
        Distribution.CENTOS_7: 'centos',
        Distribution.COREOS: 'core',
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
        VARIANT_TAG_KEY: 'ee' if enterprise else '',
        **custom_tag,
    }

    master_tags = {NODE_TYPE_TAG_KEY: NODE_TYPE_MASTER_TAG_VALUE}
    agent_tags = {NODE_TYPE_TAG_KEY: NODE_TYPE_AGENT_TAG_VALUE}
    public_agent_tags = {NODE_TYPE_TAG_KEY: NODE_TYPE_PUBLIC_AGENT_TAG_VALUE}
    cluster_backend = AWS(
        aws_key_pair=(key_name, private_key_path),
        workspace_dir=workspace_dir,
        aws_region=aws_region,
        linux_distribution=distribution,
        ec2_instance_tags=cluster_tags,
        master_ec2_instance_tags=master_tags,
        agent_ec2_instance_tags=agent_tags,
        public_agent_ec2_instance_tags=public_agent_tags,
    )

    if enterprise:
        superuser_username = 'admin'
        superuser_password = 'admin'

        enterprise_extra_config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'fault_domain_enabled': False,
        }
        if license_key is not None:
            key_contents = Path(license_key).read_text()
            enterprise_extra_config['license_key_contents'] = key_contents

        extra_config = {**enterprise_extra_config, **extra_config}
        if security_mode is not None:
            extra_config['security'] = security_mode

    try:
        cluster = Cluster(
            cluster_backend=cluster_backend,
            masters=masters,
            agents=agents,
            public_agents=public_agents,
        )
    except CalledProcessError as exc:
        click.echo('Error creating cluster.', err=True)
        click.echo(doctor_message)
        sys.exit(exc.returncode)

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

    files_to_copy_to_genconf_dir = []
    if genconf_dir is not None:
        container_genconf_path = Path('/genconf')
        for genconf_file in genconf_dir.glob('*'):
            genconf_relative = genconf_file.relative_to(genconf_dir)
            relative_path = container_genconf_path / genconf_relative
            files_to_copy_to_genconf_dir.append((genconf_file, relative_path))

    try:
        with click_spinner.spinner():
            cluster.install_dcos_from_url(
                build_artifact=artifact_url,
                dcos_config={
                    **cluster.base_config,
                    **extra_config,
                },
                ip_detect_path=cluster_backend.ip_detect_path,
                files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
            )
    except CalledProcessError as exc:
        click.echo('Error installing DC/OS.', err=True)
        click.echo(doctor_message)
        cluster.destroy()
        sys.exit(exc.returncode)
