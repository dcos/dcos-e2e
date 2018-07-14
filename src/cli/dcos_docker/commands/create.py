"""
Tools for creating a DC/OS cluster.
"""

import sys
import tempfile
import uuid
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, List, Optional, Tuple, Union

import click
import click_spinner
import docker
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from docker.models.networks import Network
from docker.types import Mount
from passlib.hash import sha512_crypt

from cli.common.options import (
    agents_option,
    artifact_argument,
    copy_to_master_option,
    extra_config_option,
    license_key_option,
    masters_option,
    public_agents_option,
    security_mode_option,
    variant_option,
    workspace_dir_option,
)
from cli.common.utils import get_variant
from cli.common.validators import (
    make_validate_cluster_id,
    validate_path_is_directory,
)
from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Transport

from ._common import (
    CLUSTER_ID_LABEL_KEY,
    DOCKER_STORAGE_DRIVERS,
    DOCKER_VERSIONS,
    LINUX_DISTRIBUTIONS,
    VARIANT_LABEL_KEY,
    WORKSPACE_DIR_LABEL_KEY,
    existing_cluster_ids,
)
from ._options import node_transport_option
from .wait import wait


def _validate_docker_network(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Any,
) -> Network:
    """
    Validate that a given network name is an existing Docker network name.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass
    client = docker.from_env(version='auto')
    try:
        return client.networks.get(network_id=value)
    except docker.errors.NotFound:
        message = (
            'No such Docker network with the name "{value}".\n'
            'Docker networks are:\n{networks}'
        ).format(
            value=value,
            networks='\n'.join(
                [network.name for network in client.networks.list()],
            ),
        )
        raise click.BadParameter(message=message)


def _validate_volumes(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Any,
) -> List[docker.types.Mount]:
    """
    Turn volume definition strings into ``Mount``s that ``docker-py`` can use.
    """
    for _ in (ctx, param):
        pass
    mounts = []
    for volume_definition in value:
        parts = volume_definition.split(':')

        if len(parts) == 1:
            host_src = None
            [container_dst] = parts
            read_only = False
        elif len(parts) == 2:
            host_src, container_dst = parts
            read_only = False
        elif len(parts) == 3:
            host_src, container_dst, mode = parts
            if mode == 'ro':
                read_only = True
            elif mode == 'rw':
                read_only = False
            else:
                message = (
                    'Mode in "{volume_definition}" is "{mode}". '
                    'If given, the mode must be one of "ro", "rw".'
                ).format(
                    volume_definition=volume_definition,
                    mode=mode,
                )
                raise click.BadParameter(message=message)
        else:
            message = (
                '"{volume_definition}" is not a valid volume definition. '
                'See '
                'https://docs.docker.com/engine/reference/run/#volume-shared-filesystems '  # noqa: E501
                'for the syntax to use.'
            ).format(volume_definition=volume_definition)
            raise click.BadParameter(message=message)

        mount = docker.types.Mount(
            source=host_src,
            target=container_dst,
            type='bind',
            read_only=read_only,
        )
        mounts.append(mount)
    return mounts


def _write_key_pair(public_key_path: Path, private_key_path: Path) -> None:
    """
    Write an RSA key pair for connecting to nodes via SSH.

    Args:
        public_key_path: Path to write public key to.
        private_key_path: Path to a private key file to write.
    """
    rsa_key_pair = rsa.generate_private_key(
        backend=default_backend(),
        public_exponent=65537,
        key_size=2048,
    )

    public_key = rsa_key_pair.public_key().public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH,
    )

    private_key = rsa_key_pair.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_key_path.write_bytes(data=public_key)
    private_key_path.write_bytes(data=private_key)


@click.command('create')
@artifact_argument
@click.option(
    '--docker-version',
    type=click.Choice(sorted(DOCKER_VERSIONS.keys())),
    default='1.13.1',
    show_default=True,
    help='The Docker version to install on the nodes.',
)
@click.option(
    '--linux-distribution',
    type=click.Choice(sorted(LINUX_DISTRIBUTIONS.keys())),
    default='centos-7',
    show_default=True,
    help='The Linux distribution to use on the nodes.',
)
@click.option(
    '--docker-storage-driver',
    type=click.Choice(sorted(DOCKER_STORAGE_DRIVERS.keys())),
    default=None,
    show_default=False,
    help=(
        'The storage driver to use for Docker in Docker. '
        "By default this uses the host's driver."
    ),
)
@masters_option
@agents_option
@public_agents_option
@extra_config_option
@security_mode_option
@click.option(
    '-c',
    '--cluster-id',
    type=str,
    default='default',
    callback=make_validate_cluster_id(
        existing_cluster_ids_func=existing_cluster_ids,
    ),
    help=(
        'A unique identifier for the cluster. '
        'Use the value "default" to use this cluster for other commands '
        'without specifying --cluster-id.'
    ),
)
@license_key_option
@click.option(
    '--genconf-dir',
    type=click.Path(exists=True),
    callback=validate_path_is_directory,
    help=(
        'Path to a directory that contains additional files for '
        'DC/OS installer. All files from this directory will be copied to the '
        '`genconf` directory before running DC/OS installer.'
    ),
)
@copy_to_master_option
@workspace_dir_option
@click.option(
    '--custom-volume',
    type=str,
    callback=_validate_volumes,
    help=(
        'Bind mount a volume on all cluster node containers. '
        'See '
        'https://docs.docker.com/engine/reference/run/#volume-shared-filesystems '  # noqa: E501
        'for the syntax to use.'
    ),
    multiple=True,
)
@click.option(
    '--custom-master-volume',
    type=str,
    callback=_validate_volumes,
    help=(
        'Bind mount a volume on all cluster master node containers. '
        'See '
        'https://docs.docker.com/engine/reference/run/#volume-shared-filesystems '  # noqa: E501
        'for the syntax to use.'
    ),
    multiple=True,
)
@click.option(
    '--custom-agent-volume',
    type=str,
    callback=_validate_volumes,
    help=(
        'Bind mount a volume on all cluster agent node containers. '
        'See '
        'https://docs.docker.com/engine/reference/run/#volume-shared-filesystems '  # noqa: E501
        'for the syntax to use.'
    ),
    multiple=True,
)
@click.option(
    '--custom-public-agent-volume',
    type=str,
    callback=_validate_volumes,
    help=(
        'Bind mount a volume on all cluster public agent node containers. '
        'See '
        'https://docs.docker.com/engine/reference/run/#volume-shared-filesystems '  # noqa: E501
        'for the syntax to use.'
    ),
    multiple=True,
)
@variant_option
@click.option(
    '--wait-for-dcos',
    is_flag=True,
    help=(
        'Wait for DC/OS after creating the cluster. '
        'This is equivalent to using "dcos-docker wait" after this command. '
        '"dcos-docker wait" has various options available and so may be more '
        'appropriate for your use case. '
        'If the chosen transport is "docker-exec", this will skip HTTP checks '
        'and so the cluster may not be fully ready.'
    ),
)
@click.option(
    '--network',
    default='bridge',
    type=str,
    callback=_validate_docker_network,
    help=(
        'The Docker network containers will be connected to.'
        'It may not be possible to SSH to containers on a custom network on '
        'macOS. '
        'Therefore, it is recommended that you use this in conjunction with '
        'the "--transport" option.'
    ),
)
@node_transport_option
@click.pass_context
def create(
    ctx: click.core.Context,
    agents: int,
    artifact: str,
    cluster_id: str,
    docker_storage_driver: str,
    docker_version: str,
    extra_config: Dict[str, Any],
    linux_distribution: str,
    masters: int,
    public_agents: int,
    license_key: Optional[str],
    security_mode: Optional[str],
    copy_to_master: List[Tuple[Path, Path]],
    genconf_dir: Optional[Path],
    workspace_dir: Optional[Path],
    custom_volume: List[Mount],
    custom_master_volume: List[Mount],
    custom_agent_volume: List[Mount],
    custom_public_agent_volume: List[Mount],
    variant: str,
    transport: Transport,
    wait_for_dcos: bool,
    network: Network,
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
    base_workspace_dir = workspace_dir or Path(tempfile.gettempdir())
    workspace_dir = base_workspace_dir / uuid.uuid4().hex

    doctor_message = 'Try `dcos-docker doctor` for troubleshooting help.'
    ssh_keypair_dir = workspace_dir / 'ssh'
    ssh_keypair_dir.mkdir(parents=True)
    public_key_path = ssh_keypair_dir / 'id_rsa.pub'
    private_key_path = ssh_keypair_dir / 'id_rsa'
    _write_key_pair(
        public_key_path=public_key_path,
        private_key_path=private_key_path,
    )

    artifact_path = Path(artifact).resolve()

    if variant == 'auto':
        variant = get_variant(
            artifact_path=artifact_path,
            workspace_dir=workspace_dir,
            doctor_message=doctor_message,
        )

    enterprise = bool(variant == 'enterprise')
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

    files_to_copy_to_installer = []
    if genconf_dir is not None:
        container_genconf_path = Path('/genconf')
        for genconf_file in genconf_dir.glob('*'):
            genconf_relative = genconf_file.relative_to(genconf_dir)
            relative_path = container_genconf_path / genconf_relative
            files_to_copy_to_installer.append((genconf_file, relative_path))

    cluster_backend = Docker(
        custom_container_mounts=custom_volume,
        custom_master_mounts=custom_master_volume,
        custom_agent_mounts=custom_agent_volume,
        custom_public_agent_mounts=custom_public_agent_volume,
        linux_distribution=LINUX_DISTRIBUTIONS[linux_distribution],
        docker_version=DOCKER_VERSIONS[docker_version],
        storage_driver=DOCKER_STORAGE_DRIVERS.get(docker_storage_driver),
        docker_container_labels={
            CLUSTER_ID_LABEL_KEY: cluster_id,
            WORKSPACE_DIR_LABEL_KEY: str(workspace_dir),
            VARIANT_LABEL_KEY: 'ee' if enterprise else '',
        },
        docker_master_labels={'node_type': 'master'},
        docker_agent_labels={'node_type': 'agent'},
        docker_public_agent_labels={'node_type': 'public_agent'},
        workspace_dir=workspace_dir,
        transport=transport,
        network=network,
    )

    try:
        cluster = Cluster(
            cluster_backend=cluster_backend,
            masters=masters,
            agents=agents,
            public_agents=public_agents,
            files_to_copy_to_installer=files_to_copy_to_installer,
        )
    except CalledProcessError as exc:
        click.echo('Error creating cluster.', err=True)
        click.echo(doctor_message)
        sys.exit(exc.returncode)

    nodes = {
        *cluster.masters,
        *cluster.agents,
        *cluster.public_agents,
    }

    for node in nodes:
        node.run(
            args=['echo', '', '>>', '/root/.ssh/authorized_keys'],
            shell=True,
        )
        node.run(
            args=[
                'echo',
                public_key_path.read_text(),
                '>>',
                '/root/.ssh/authorized_keys',
            ],
            shell=True,
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
            cluster.install_dcos_from_path(
                build_artifact=artifact_path,
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

    click.echo(cluster_id)

    if wait_for_dcos:
        ctx.invoke(
            wait,
            cluster_id=cluster_id,
            transport=transport,
            skip_http_checks=bool(transport == Transport.DOCKER_EXEC),
        )
        return

    started_message = (
        'Cluster "{cluster_id}" has started. '
        'Run "dcos-docker wait --cluster-id {cluster_id}" to wait for DC/OS '
        'to become ready.'
    ).format(cluster_id=cluster_id)
    click.echo(started_message, err=True)
