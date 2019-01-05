"""
Common code for minidcos docker CLI modules.
"""

import sys
from ipaddress import IPv4Address
from pathlib import Path
from shutil import rmtree
from typing import Dict, List, Set

import click
import docker
from docker.client import DockerClient
from docker.models.containers import Container

from dcos_e2e.cluster import Cluster
from dcos_e2e.distributions import Distribution
from dcos_e2e.docker_storage_drivers import DockerStorageDriver
from dcos_e2e.docker_versions import DockerVersion
from dcos_e2e.node import Node, Role, Transport
from dcos_e2e_cli._vendor.dcos_installer_tools import DCOSVariant

LINUX_DISTRIBUTIONS = {
    'centos-7': Distribution.CENTOS_7,
    'coreos': Distribution.COREOS,
    'ubuntu-16.04': Distribution.UBUNTU_16_04,
}

DOCKER_VERSIONS = {
    '1.11.2': DockerVersion.v1_11_2,
    '1.13.1': DockerVersion.v1_13_1,
    '17.12.1-ce': DockerVersion.v17_12_1_ce,
}

DOCKER_STORAGE_DRIVERS = {
    'aufs': DockerStorageDriver.AUFS,
    'overlay': DockerStorageDriver.OVERLAY,
    'overlay2': DockerStorageDriver.OVERLAY_2,
}

CLUSTER_ID_LABEL_KEY = 'dcos_e2e.cluster_id'
SIDECAR_NAME_LABEL_KEY = 'dcos_e2e.sidecar_name'
WORKSPACE_DIR_LABEL_KEY = 'dcos_e2e.workspace_dir'
VARIANT_LABEL_KEY = 'dcos_e2e.variant'
VARIANT_ENTERPRISE_LABEL_VALUE = 'ee'
VARIANT_OSS_LABEL_VALUE = 'oss'
NODE_TYPE_LABEL_KEY = 'dcos_e2e.node_type'
NODE_TYPE_MASTER_LABEL_VALUE = 'master'
NODE_TYPE_AGENT_LABEL_VALUE = 'agent'
NODE_TYPE_PUBLIC_AGENT_LABEL_VALUE = 'public_agent'
NODE_TYPE_LOOPBACK_SIDECAR_LABEL_VALUE = 'loopback'


def docker_client() -> DockerClient:
    """
    Return a Docker client.
    """
    try:
        return docker.from_env(version='auto')
    except docker.errors.DockerException:
        message = (
            'Error: Cannot connect to Docker.\n'
            'Make sure that Docker is installed and running, '
            'and that you can run "docker ps".\n'
            'If "sudo docker ps" works, try following the instructions at '
            'https://docs.docker.com/install/linux/linux-postinstall/.'
        )
        click.echo(message, err=True)
        sys.exit(1)


def existing_cluster_ids() -> Set[str]:
    """
    Return the IDs of existing clusters.
    """
    client = docker_client()
    filters = {'label': CLUSTER_ID_LABEL_KEY}
    containers = client.containers.list(filters=filters)
    return set(
        container.labels[CLUSTER_ID_LABEL_KEY] for container in containers
    )


def loopback_sidecars_by_name(name: str) -> List[Container]:
    """
    Return all loopback sidecar containers with the given sidecar ``name``.
    """
    client = docker_client()
    filters = {
        'label': [
            '{key}={value}'.format(
                key=NODE_TYPE_LABEL_KEY,
                value=NODE_TYPE_LOOPBACK_SIDECAR_LABEL_VALUE,
            ),
            '{key}={value}'.format(
                key=SIDECAR_NAME_LABEL_KEY,
                value=name,
            ),
        ],
    }
    return list(client.containers.list(filters=filters))


class ContainerInspectView:
    """
    Details of a node from a container.
    """

    def __init__(self, container: Container) -> None:
        """
        Args:
            container: The Docker container which represents the node.
        """
        self._container = container

    def to_dict(self) -> Dict[str, str]:
        """
        Return dictionary with information to be shown to users.
        """
        container = self._container
        role = container.labels[NODE_TYPE_LABEL_KEY]
        container_ip = container.attrs['NetworkSettings']['IPAddress']
        cluster_containers = ClusterContainers(
            cluster_id=container.labels[CLUSTER_ID_LABEL_KEY],
            transport=Transport.DOCKER_EXEC,
        )

        containers = {
            NODE_TYPE_MASTER_LABEL_VALUE: cluster_containers.masters,
            NODE_TYPE_AGENT_LABEL_VALUE: cluster_containers.agents,
            NODE_TYPE_PUBLIC_AGENT_LABEL_VALUE:
            cluster_containers.public_agents,
        }[role]

        sorted_ips = sorted(
            [ctr.attrs['NetworkSettings']['IPAddress'] for ctr in containers],
        )

        index = sorted_ips.index(container_ip)

        return {
            'e2e_reference': '{role}_{index}'.format(role=role, index=index),
            'docker_container_name': container.name,
            'docker_container_id': container.id,
            'ip_address': container_ip,
        }


class ClusterContainers:
    """
    A representation of a cluster constructed from Docker nodes.
    """

    def __init__(self, cluster_id: str, transport: Transport) -> None:
        """
        Args:
            cluster_id: The ID of the cluster.
            transport: The transport to use for communication with nodes.
        """
        self._cluster_id_label = CLUSTER_ID_LABEL_KEY + '=' + cluster_id
        self._transport = transport

    def _containers_by_role(
        self,
        role: Role,
    ) -> Set[Container]:
        """
        Return all containers in this cluster of a particular node type.
        """
        node_types = {
            Role.MASTER: NODE_TYPE_MASTER_LABEL_VALUE,
            Role.AGENT: NODE_TYPE_AGENT_LABEL_VALUE,
            Role.PUBLIC_AGENT: NODE_TYPE_PUBLIC_AGENT_LABEL_VALUE,
        }
        client = docker_client()
        filters = {
            'label': [
                self._cluster_id_label,
                '{key}={value}'.format(
                    key=NODE_TYPE_LABEL_KEY,
                    value=node_types[role],
                ),
            ],
        }
        return set(client.containers.list(filters=filters))

    def to_node(self, container: Container) -> Node:
        """
        Return the ``Node`` that is represented by a given ``container``.
        """
        address = IPv4Address(container.attrs['NetworkSettings']['IPAddress'])
        ssh_key_path = self.workspace_dir / 'ssh' / 'id_rsa'
        return Node(
            public_ip_address=address,
            private_ip_address=address,
            default_user='root',
            ssh_key_path=ssh_key_path,
            default_transport=self._transport,
        )

    @property
    def masters(self) -> Set[Container]:
        """
        Docker containers which represent master nodes.
        """
        return self._containers_by_role(role=Role.MASTER)

    @property
    def agents(self) -> Set[Container]:
        """
        Docker containers which represent agent nodes.
        """
        return self._containers_by_role(role=Role.AGENT)

    @property
    def public_agents(self) -> Set[Container]:
        """
        Docker containers which represent public agent nodes.
        """
        return self._containers_by_role(role=Role.PUBLIC_AGENT)

    @property
    def dcos_variant(self) -> DCOSVariant:
        """
        Return the DC/OS variant of the cluster.
        """
        master_container = next(iter(self.masters))
        container_variant_value = master_container.labels[VARIANT_LABEL_KEY]
        return {
            VARIANT_ENTERPRISE_LABEL_VALUE: DCOSVariant.ENTERPRISE,
            VARIANT_OSS_LABEL_VALUE: DCOSVariant.OSS,
        }[container_variant_value]

    @property
    def cluster(self) -> Cluster:
        """
        Return a ``Cluster`` constructed from the containers.
        """
        return Cluster.from_nodes(
            masters=set(map(self.to_node, self.masters)),
            agents=set(map(self.to_node, self.agents)),
            public_agents=set(map(self.to_node, self.public_agents)),
        )

    @property
    def workspace_dir(self) -> Path:
        """
        The workspace directory to put temporary files in.
        """
        container = next(iter(self.masters))
        workspace_dir = container.labels[WORKSPACE_DIR_LABEL_KEY]
        return Path(workspace_dir)

    def destroy(self) -> None:
        """
        Destroy this cluster.
        """
        containers = {
            *self.masters,
            *self.agents,
            *self.public_agents,
        }
        rmtree(path=str(self.workspace_dir), ignore_errors=True)
        for container in containers:
            container.stop()
            container.remove(v=True)
