"""
Tools for creating a DC/OS cluster.
"""
import sys
import tempfile
import uuid
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, List, Optional, Tuple

import click
import click_spinner
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from docker.types import Mount
from passlib.hash import sha512_crypt

from cli._common import (
    CLUSTER_ID_LABEL_KEY,
    DOCKER_STORAGE_DRIVERS,
    DOCKER_VERSIONS,
    LINUX_DISTRIBUTIONS,
    VARIANT_LABEL_KEY,
    WORKSPACE_DIR_LABEL_KEY,
)
from cli._options import node_transport_option
from cli._validators import (
    validate_cluster_id,
    validate_dcos_configuration,
    validate_path_is_directory,
    validate_path_pair,
    validate_volumes,
)
from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Transport


def _get_variant(artifact_path: Path, workspace_dir: Path) -> str:
    """
    Get the variant of a DC/OS artifact.

    Args:
        artifact_path: The path to an artifact to get the DC/OS variant of.
        workspace_dir: A directory to work in, given that this function uses
            large files.

    Returns:
        "oss" or "enterprise" as appropriate.

    Raises:
        CalledProcessError: There was an error unpacking the artifact.
    """
    doctor_message = 'Try `dcos-docker doctor` for troubleshooting help.'

    try:
        with click_spinner.spinner():
            enterprise = is_enterprise(
                build_artifact=artifact_path,
                workspace_dir=workspace_dir,
            )
    except subprocess.CalledProcessError as exc:
        rmtree(path=str(workspace_dir), ignore_errors=True)
        click.echo(doctor_message)
        click.echo()
        click.echo('Original error:', err=True)
        click.echo(exc.stderr, err=True)
        raise
    except ValueError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    return 'enterprise' if enterprise else 'oss'


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
@click.argument('artifact', type=click.Path(exists=True))
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
@click.option(
    '--masters',
    type=click.INT,
    default=1,
    show_default=True,
    help='The number of master nodes.',
)
@click.option(
    '--agents',
    type=click.INT,
    default=1,
    show_default=True,
    help='The number of agent nodes.',
)
@click.option(
    '--public-agents',
    type=click.INT,
    default=1,
    show_default=True,
    help='The number of public agent nodes.',
)
@click.option(
    '--extra-config',
    type=click.Path(exists=True),
    callback=validate_dcos_configuration,
    help=(
        'The path to a file including DC/OS configuration YAML. '
        'The contents of this file will be added to add to a default '
        'configuration.'
    ),
)
@click.option(
    '--security-mode',
    type=click.Choice(['disabled', 'permissive', 'strict']),
    help=(
        'The security mode to use for a DC/OS Enterprise cluster. '
        'This overrides any security mode set in ``--extra-config``.'
    ),
)
@click.option(
    '-c',
    '--cluster-id',
    type=str,
    default='default',
    callback=validate_cluster_id,
    help=(
        'A unique identifier for the cluster. '
        'Use the value "default" to use this cluster for other commands '
        'without specifying --cluster-id.'
    ),
)
@click.option(
    '--license-key',
    type=click.Path(exists=True),
    envvar='DCOS_LICENSE_KEY_PATH',
    help=(
        'This is ignored if using open source DC/OS. '
        'If using DC/OS Enterprise, this defaults to the value of the '
        '`DCOS_LICENSE_KEY_PATH` environment variable.'
    ),
)
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
@click.option(
    '--copy-to-master',
    type=str,
    callback=validate_path_pair,
    multiple=True,
    help=(
        'Files to copy to master nodes before installing DC/OS. '
        'This option can be given multiple times. '
        'Each option should be in the format '
        '/absolute/local/path:/remote/path.'
    ),
)
@click.option(
    '--workspace-dir',
    type=click.Path(exists=True),
    callback=validate_path_is_directory,
    help=(
        'Creating a cluster can use approximately 2 GB of temporary storage. '
        'Set this option to use a custom "workspace" for this temporary '
        'storage. '
        'See '
        'https://docs.python.org/3/library/tempfile.html#tempfile.gettempdir '
        'for details on the temporary directory location if this option is '
        'not set.'
    ),
)
@click.option(
    '--custom-volume',
    type=str,
    callback=validate_volumes,
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
    callback=validate_volumes,
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
    callback=validate_volumes,
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
    callback=validate_volumes,
    help=(
        'Bind mount a volume on all cluster public agent node containers. '
        'See '
        'https://docs.docker.com/engine/reference/run/#volume-shared-filesystems '  # noqa: E501
        'for the syntax to use.'
    ),
    multiple=True,
)
@click.option(
    '--variant',
    type=click.Choice(['auto', 'oss', 'enterprise']),
    default='auto',
    help=(
        'Choose the DC/OS variant. '
        'If the variant does not match the variant of the given artifact, '
        'an error will occur. '
        'Using "auto" finds the variant from the artifact. '
        'Finding the variant from the artifact takes some time and so using '
        'another option is a performance optimization.'
    ),
)
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
    enterprise = bool(variant == 'enterprise')

    if variant == 'auto':
        variant = _get_variant(
            artifact_path=artifact_path,
            workspace_dir=workspace_dir,
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
