"""
Common code for minidcos docker CLI modules.
"""

import functools
import sys
from ipaddress import IPv4Address
from pathlib import Path
from shutil import rmtree
from typing import Any, Dict, Set

import click
import docker
from docker.client import DockerClient
from docker.models.containers import Container

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node, Role, Transport
from dcos_e2e_cli.common.base_classes import ClusterRepresentation

CLUSTER_ID_LABEL_KEY = 'dcos_e2e.cluster_id'
SIDECAR_NAME_LABEL_KEY = 'dcos_e2e.sidecar_name'
WORKSPACE_DIR_LABEL_KEY = 'dcos_e2e.workspace_dir'
NODE_TYPE_LABEL_KEY = 'dcos_e2e.node_type'
NODE_TYPE_MASTER_LABEL_VALUE = 'master'
NODE_TYPE_AGENT_LABEL_VALUE = 'agent'
NODE_TYPE_PUBLIC_AGENT_LABEL_VALUE = 'public_agent'
NODE_TYPE_LOOPBACK_SIDECAR_LABEL_VALUE = 'loopback'


@functools.lru_cache()
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


class ClusterContainers(ClusterRepresentation):
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

    @functools.lru_cache()
    def _containers_by_role(self, role: Role) -> Set[Container]:
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

    def to_node(self, node_representation: Container) -> Node:
        """
        Return the ``Node`` that is represented by a given ``container``.
        """
        container = node_representation
        networks = container.attrs['NetworkSettings']['Networks']
        network_name = 'bridge'
        if len(networks) != 1:
            [network_name] = list(networks.keys() - set(['bridge']))
        address = IPv4Address(networks[network_name]['IPAddress'])
        return Node(
            public_ip_address=address,
            private_ip_address=address,
            default_user=self._ssh_default_user,
            ssh_key_path=self.ssh_key_path,
            default_transport=self._transport,
        )

    def to_dict(self, node_representation: Container) -> Dict[str, str]:
        """
        Return information to be shown to users which is unique to this node.
        """
        container = node_representation
        role = container.labels[NODE_TYPE_LABEL_KEY]
        container_ip = container.attrs['NetworkSettings']['IPAddress']

        containers = {
            NODE_TYPE_MASTER_LABEL_VALUE: self.masters,
            NODE_TYPE_AGENT_LABEL_VALUE: self.agents,
            NODE_TYPE_PUBLIC_AGENT_LABEL_VALUE: self.public_agents,
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
            'ssh_user': self._ssh_default_user,
            'ssh_key': str(self.ssh_key_path),
        }

    @property
    def _ssh_default_user(self) -> str:
        """
        A user which can be used to SSH to any node using
        ``self.ssh_key_path``.
        """
        return 'root'

    @property
    def ssh_key_path(self) -> Path:
        """
        A key which can be used to SSH to any node.
        """
        return self._workspace_dir / 'ssh' / 'id_rsa'

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
    def _workspace_dir(self) -> Path:
        """
        The workspace directory to put temporary files in.
        """
        container = next(iter(self.masters))
        workspace_dir = container.labels[WORKSPACE_DIR_LABEL_KEY]
        return Path(workspace_dir)

    @property
    def base_config(self) -> Dict[str, Any]:
        """
        Return a base configuration for installing DC/OS OSS.
        """
        backend = Docker()

        return {
            **self.cluster.base_config,
            **backend.base_config,
        }

    def destroy(self) -> None:
        """
        Destroy this cluster.
        """
        containers = {
            *self.masters,
            *self.agents,
            *self.public_agents,
        }
        rmtree(path=str(self._workspace_dir), ignore_errors=True)
        for container in containers:
            container.stop()
            container.remove(v=True)
