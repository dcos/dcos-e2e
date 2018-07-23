"""
Tools for creating a DC/OS cluster.
"""

import sys
from ipaddress import IPv4Address
import tempfile
import uuid
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, List, Optional, Tuple

import boto3
import click
import click_spinner
from passlib.hash import sha512_crypt

from cli.common.options import (
    agents_option,
    copy_to_master_option,
    extra_config_option,
    license_key_option,
    masters_option,
    public_agents_option,
    security_mode_option,
    verbosity_option,
    workspace_dir_option,
)
from cli.common.utils import set_logging
from dcos_e2e.backends import AWS
from dcos_e2e.cluster import Cluster


@click.command('create')
@click.argument(
    'artifact_url',
    type=str,
)
@click.option(
    '--variant',
    type=click.Choice(['oss', 'enterprise']),
    default='oss',
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
@workspace_dir_option
@license_key_option
@security_mode_option
@copy_to_master_option
@verbosity_option
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
    base_workspace_dir = workspace_dir or Path(tempfile.gettempdir())
    workspace_dir = base_workspace_dir / uuid.uuid4().hex
    workspace_dir.mkdir(parents=True)

    doctor_message = 'Try `dcos-aws doctor` for troubleshooting help.'
    enterprise = bool(variant == 'enterprise')
    cluster_backend = AWS(workspace_dir=workspace_dir)

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
            files_to_copy_to_installer=[],
        )
    except CalledProcessError as exc:
        click.echo('Error creating cluster.', err=True)
        click.echo(doctor_message)
        sys.exit(exc.returncode)

    ec2 = boto3.resource('ec2', region_name=cluster_backend.aws_region)
    ec2_instances = ec2.instances.all()

    nodes = {*cluster.masters, *cluster.agents, *cluster.public_agents}
    node_public_ips = set([node.public_ip_address for node in nodes])
    node_ec2_instance_ids = [
        instance.id for instance in ec2_instances
        if IPv4Address(instance.public_ip_address) in node_public_ips
    ]

    cluster_id = 'a'
    CLUSTER_ID_TAG_KEY = 'a'
    cluster_id_tag = {
        'Key': CLUSTER_ID_TAG_KEY,
        'Value': cluster_id,
    }

    ec2.create_tags(
        Resources=node_ec2_instance_ids,
        Tags=[cluster_id_tag]
    )

    for node in cluster.masters:
        for path_pair in copy_to_master:
            local_path, remote_path = path_pair
            node.send_file(
                local_path=local_path,
                remote_path=remote_path,
            )

    try:
        with click_spinner.spinner():
            cluster.install_dcos_from_url(
                build_artifact=artifact_url,
                dcos_config={
                    **cluster.base_config,
                    **extra_config,
                },
            )
    except CalledProcessError as exc:
        click.echo('Error installing DC/OS.', err=True)
        click.echo(doctor_message)
        cluster.destroy()
        sys.exit(exc.returncode)
