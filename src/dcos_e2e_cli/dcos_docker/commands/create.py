"""
Tools for creating a DC/OS cluster.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import click
import docker
from docker.models.networks import Network
from docker.types import Mount

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Transport
from dcos_e2e_cli.common.arguments import installer_argument
from dcos_e2e_cli.common.create import create_cluster, get_config
from dcos_e2e_cli.common.doctor import get_doctor_message
from dcos_e2e_cli.common.install import (
    install_dcos_from_path,
    run_post_install_steps,
)
from dcos_e2e_cli.common.options import (
    agents_option,
    cluster_id_option,
    copy_to_master_option,
    extra_config_option,
    genconf_dir_option,
    license_key_option,
    masters_option,
    public_agents_option,
    security_mode_option,
    variant_option,
    verbosity_option,
)
from dcos_e2e_cli.common.utils import (
    check_cluster_id_unique,
    command_path,
    write_key_pair,
)
from dcos_e2e_cli.common.variants import get_install_variant
from dcos_e2e_cli.common.workspaces import workspace_dir_option

from ._common import (
    CLUSTER_ID_LABEL_KEY,
    DOCKER_STORAGE_DRIVERS,
    DOCKER_VERSIONS,
    LINUX_DISTRIBUTIONS,
    NODE_TYPE_AGENT_LABEL_VALUE,
    NODE_TYPE_LABEL_KEY,
    NODE_TYPE_MASTER_LABEL_VALUE,
    NODE_TYPE_PUBLIC_AGENT_LABEL_VALUE,
    WORKSPACE_DIR_LABEL_KEY,
    ClusterContainers,
    docker_client,
    existing_cluster_ids,
)
from ._options import node_transport_option, wait_for_dcos_option
from ._port_mapping import one_master_host_port_map_option
from ._volume_options import (
    AGENT_VOLUME_OPTION,
    MASTER_VOLUME_OPTION,
    PUBLIC_AGENT_VOLUME_OPTION,
    VOLUME_OPTION,
)
from .doctor import doctor
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
    client = docker_client()
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


def _add_authorized_key(cluster: Cluster, public_key_path: Path) -> None:
    """
    Add an authorized key to all nodes in the given cluster.
    """
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


@click.command('create')
@installer_argument
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
    '--mount-sys-fs-cgroup/--no-mount-sys-fs-cgroup',
    default=True,
    show_default=True,
    help=(
        'Mounting ``/sys/fs/cgroup`` from the host is required to run '
        'applications which require ``cgroup`` isolation. '
        'Choose to not mount ``/sys/fs/cgroup`` if it is not available on the '
        'host.'
    ),
)
@masters_option
@agents_option
@public_agents_option
@extra_config_option
@security_mode_option
@cluster_id_option
@license_key_option
@genconf_dir_option
@copy_to_master_option
@VOLUME_OPTION
@MASTER_VOLUME_OPTION
@AGENT_VOLUME_OPTION
@PUBLIC_AGENT_VOLUME_OPTION
@workspace_dir_option
@variant_option
@wait_for_dcos_option
@click.option(
    '--network',
    default='bridge',
    type=str,
    callback=_validate_docker_network,
    help=(
        'The Docker network containers will be connected to.'
        'It may not be possible to SSH to containers on a custom network on '
        'macOS. '
    ),
)
@node_transport_option
@one_master_host_port_map_option
@verbosity_option
@click.pass_context
def create(
    ctx: click.core.Context,
    agents: int,
    installer: str,
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
    workspace_dir: Path,
    custom_volume: List[Mount],
    custom_master_volume: List[Mount],
    custom_agent_volume: List[Mount],
    custom_public_agent_volume: List[Mount],
    variant: str,
    transport: Transport,
    wait_for_dcos: bool,
    network: Network,
    one_master_host_port_map: Dict[str, int],
    mount_sys_fs_cgroup: bool,
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
    check_cluster_id_unique(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )

    http_checks = bool(transport == Transport.SSH)
    wait_command_name = command_path(sibling_ctx=ctx, command=wait)
    doctor_command_name = command_path(sibling_ctx=ctx, command=doctor)
    doctor_message = get_doctor_message(
        doctor_command_name=doctor_command_name,
    )
    ssh_keypair_dir = workspace_dir / 'ssh'
    ssh_keypair_dir.mkdir(parents=True)
    public_key_path = ssh_keypair_dir / 'id_rsa.pub'
    private_key_path = ssh_keypair_dir / 'id_rsa'
    write_key_pair(
        public_key_path=public_key_path,
        private_key_path=private_key_path,
    )

    installer_path = Path(installer).resolve()

    dcos_variant = get_install_variant(
        given_variant=variant,
        installer_path=installer_path,
        workspace_dir=workspace_dir,
        doctor_message=doctor_message,
    )

    # This is useful for some people to identify containers.
    container_name_prefix = Docker().container_name_prefix + '-' + cluster_id

    cluster_backend = Docker(
        container_name_prefix=container_name_prefix,
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
        },
        docker_master_labels={
            NODE_TYPE_LABEL_KEY: NODE_TYPE_MASTER_LABEL_VALUE,
        },
        docker_agent_labels={NODE_TYPE_LABEL_KEY: NODE_TYPE_AGENT_LABEL_VALUE},
        docker_public_agent_labels={
            NODE_TYPE_LABEL_KEY: NODE_TYPE_PUBLIC_AGENT_LABEL_VALUE,
        },
        workspace_dir=workspace_dir,
        transport=transport,
        network=network,
        one_master_host_port_map=one_master_host_port_map,
        mount_sys_fs_cgroup=mount_sys_fs_cgroup,
    )

    cluster = create_cluster(
        cluster_backend=cluster_backend,
        masters=masters,
        agents=agents,
        public_agents=public_agents,
        doctor_message=doctor_message,
    )

    _add_authorized_key(cluster=cluster, public_key_path=public_key_path)

    for node in cluster.masters:
        for path_pair in copy_to_master:
            local_path, remote_path = path_pair
            node.send_file(
                local_path=local_path,
                remote_path=remote_path,
            )

    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        transport=transport,
    )

    dcos_config = get_config(
        cluster_representation=cluster_containers,
        extra_config=extra_config,
        dcos_variant=dcos_variant,
        security_mode=security_mode,
        license_key=license_key,
    )

    install_dcos_from_path(
        cluster_representation=cluster_containers,
        dcos_config=dcos_config,
        ip_detect_path=cluster_backend.ip_detect_path,
        doctor_message=doctor_message,
        dcos_installer=installer_path,
        local_genconf_dir=genconf_dir,
    )

    run_post_install_steps(
        cluster=cluster,
        cluster_id=cluster_id,
        dcos_config=dcos_config,
        doctor_command_name=doctor_command_name,
        http_checks=http_checks,
        wait_command_name=wait_command_name,
        wait_for_dcos=wait_for_dcos,
    )
