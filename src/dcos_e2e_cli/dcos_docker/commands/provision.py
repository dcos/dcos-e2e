"""
Tools for provisioning a bare Docker cluster.
"""

from pathlib import Path
from typing import Dict, List, Optional

import click
from docker.models.networks import Network
from docker.types import Mount

from dcos_e2e.backends import Docker
from dcos_e2e.distributions import Distribution
from dcos_e2e.docker_storage_drivers import DockerStorageDriver
from dcos_e2e.docker_versions import DockerVersion
from dcos_e2e.node import Transport
from dcos_e2e_cli.common.create import create_cluster
from dcos_e2e_cli.common.credentials import add_authorized_key
from dcos_e2e_cli.common.doctor import get_doctor_message
from dcos_e2e_cli.common.options import (
    cluster_id_option,
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

from ._cgroup_mount_option import cgroup_mount_option
from ._common import (
    CLUSTER_ID_LABEL_KEY,
    NODE_TYPE_AGENT_LABEL_VALUE,
    NODE_TYPE_LABEL_KEY,
    NODE_TYPE_MASTER_LABEL_VALUE,
    NODE_TYPE_PUBLIC_AGENT_LABEL_VALUE,
    WORKSPACE_DIR_LABEL_KEY,
    ClusterContainers,
    existing_cluster_ids,
)
from ._docker_network import docker_network_option
from ._docker_storage_driver import docker_storage_driver_option
from ._docker_version import docker_version_option
from ._linux_distribution import linux_distribution_option
from ._options import node_transport_option
from ._port_mapping import one_master_host_port_map_option
from ._volume_options import (
    AGENT_VOLUME_OPTION,
    MASTER_VOLUME_OPTION,
    PUBLIC_AGENT_VOLUME_OPTION,
    VOLUME_OPTION,
)
from .doctor import doctor


@click.command('provision')
@docker_version_option
@linux_distribution_option
@docker_storage_driver_option
@cgroup_mount_option
@masters_option
@agents_option
@public_agents_option
@cluster_id_option
@VOLUME_OPTION
@MASTER_VOLUME_OPTION
@AGENT_VOLUME_OPTION
@PUBLIC_AGENT_VOLUME_OPTION
@workspace_dir_option
@docker_network_option
@node_transport_option
@one_master_host_port_map_option
@verbosity_option
@enable_spinner_option
@click.pass_context
def provision(
    ctx: click.core.Context,
    agents: int,
    cluster_id: str,
    docker_storage_driver: Optional[DockerStorageDriver],
    docker_version: DockerVersion,
    linux_distribution: Distribution,
    masters: int,
    public_agents: int,
    workspace_dir: Path,
    custom_volume: List[Mount],
    custom_master_volume: List[Mount],
    custom_agent_volume: List[Mount],
    custom_public_agent_volume: List[Mount],
    transport: Transport,
    network: Network,
    one_master_host_port_map: Dict[str, int],
    mount_sys_fs_cgroup: bool,
    enable_spinner: bool,
) -> None:
    """
    Provision Docker containers to install a DC/OS cluster.
    """
    check_cluster_id_unique(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )

    doctor_command_name = command_path(sibling_ctx=ctx, command=doctor)
    doctor_message = get_doctor_message(
        doctor_command_name=doctor_command_name,
    )
    public_key_path = workspace_dir / 'id_rsa.pub'
    private_key_path = workspace_dir / 'id_rsa'
    write_key_pair(
        public_key_path=public_key_path,
        private_key_path=private_key_path,
    )

    # This is useful for some people to identify containers.
    container_name_prefix = Docker().container_name_prefix + '-' + cluster_id

    cluster_backend = Docker(
        container_name_prefix=container_name_prefix,
        custom_container_mounts=custom_volume,
        custom_master_mounts=custom_master_volume,
        custom_agent_mounts=custom_agent_volume,
        custom_public_agent_mounts=custom_public_agent_volume,
        linux_distribution=linux_distribution,
        docker_version=docker_version,
        storage_driver=docker_storage_driver,
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
        enable_spinner=enable_spinner,
    )

    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        transport=transport,
    )
    private_ssh_key_path = cluster_containers.ssh_key_path
    private_ssh_key_path.parent.mkdir(parents=True)
    private_key_path.replace(private_ssh_key_path)

    add_authorized_key(cluster=cluster, public_key_path=public_key_path)
