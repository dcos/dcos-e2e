"""
Common code for CLI modules.
"""

from ipaddress import IPv4Address
from pathlib import Path
from typing import Dict, Set

import docker
from docker.models.containers import Container

from dcos_e2e.cluster import Cluster
from dcos_e2e.distributions import Distribution
from dcos_e2e.docker_storage_drivers import DockerStorageDriver
from dcos_e2e.docker_versions import DockerVersion
from dcos_e2e.node import Node

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
WORKSPACE_DIR_LABEL_KEY = 'dcos_e2e.workspace_dir'
VARIANT_LABEL_KEY = 'dcos_e2e.variant'


def existing_cluster_ids() -> Set[str]:
    """
    Return the IDs of existing clusters.
    """
    client = docker.from_env(version='auto')
    filters = {'label': CLUSTER_ID_LABEL_KEY}
    containers = client.containers.list(filters=filters)
    return set(
        [container.labels[CLUSTER_ID_LABEL_KEY] for container in containers],
    )


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
        index = container.name.split('-')[-1]
        name_without_index = container.name[:-len('-' + index)]
        if name_without_index.endswith('public-agent'):
            role = 'public_agent'
        elif name_without_index.endswith('agent'):
            role = 'agent'
        elif name_without_index.endswith('master'):
            role = 'master'

        return {
            'e2e_reference': '{role}_{index}'.format(role=role, index=index),
            'docker_container_name': container.name,
            'ip_address': container.attrs['NetworkSettings']['IPAddress'],
        }


class ClusterContainers:
    """
    A representation of a cluster constructed from Docker nodes.
    """

    def __init__(self, cluster_id: str) -> None:
        """
        Args:
            cluster_id: The ID of the cluster.
        """
        self._cluster_id_label = CLUSTER_ID_LABEL_KEY + '=' + cluster_id

    def _containers_by_node_type(
        self,
        node_type: str,
    ) -> Set[Container]:
        """
        Return all containers in this cluster of a particular node type.
        """
        client = docker.from_env(version='auto')
        filters = {
            'label': [
                self._cluster_id_label,
                'node_type={node_type}'.format(node_type=node_type),
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
            default_ssh_user='root',
            ssh_key_path=ssh_key_path,
        )

    @property
    def masters(self) -> Set[Container]:
        """
        Docker containers which represent master nodes.
        """
        return self._containers_by_node_type(node_type='master')

    @property
    def agents(self) -> Set[Container]:
        """
        Docker containers which represent agent nodes.
        """
        return self._containers_by_node_type(node_type='agent')

    @property
    def public_agents(self) -> Set[Container]:
        """
        Docker containers which represent public agent nodes.
        """
        return self._containers_by_node_type(node_type='public_agent')

    @property
    def is_enterprise(self) -> bool:
        """
        Return whether the cluster is a DC/OS Enterprise cluster.
        """
        master_container = next(iter(self.masters))
        return bool(master_container.labels[VARIANT_LABEL_KEY] == 'ee')

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
        container = next(iter(self.masters))
        workspace_dir = container.labels[WORKSPACE_DIR_LABEL_KEY]
        return Path(workspace_dir)
