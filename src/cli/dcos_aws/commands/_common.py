"""
Common code for dcos-docker CLI modules.
"""

from typing import Set

import boto3
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node, Role

CLUSTER_ID_TAG_KEY = 'dcos_e2e.cluster_id'
NODE_TYPE_TAG_KEY = 'dcos_e2e.node_type'


def existing_cluster_ids(aws_region: str) -> Set[str]:
    """
    Return the IDs of existing clusters.

    Args:
        aws_region: The region to get clusters from.
    """
    ec2 = boto3.resource('ec2', region_name=aws_region)
    ec2_instances = ec2.instances.all()

    cluster_ids = set()  # type: Set[str]
    for instance in ec2_instances:
        for tag in instance.tags:
            if tag['Key'] == CLUSTER_ID_TAG_KEY:
                cluster_ids.add(tag['Value'])

    return cluster_ids


class ClusterInstances:
    """
    A representation of a cluster constructed from EC2 instances.
    """

    def __init__(self, cluster_id: str, aws_region: str) -> None:
        """
        Args:
            cluster_id: The ID of the cluster.
            aws_region: The AWS region the cluster is in.
        """
        self.cluster_id = cluster_id
        self.aws_region = aws_region

    def _instances_by_role(
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

    def to_node(self, instance: Container) -> Node:
        """
        Return the ``Node`` that is represented by a given ``container``.
        """
        public_ip_address = instance.public_ip_address
        private_ip_address = instance.public_ip_address
        ssh_key_path = self.workspace_dir / 'ssh' / 'id_rsa'
        return Node(
            public_ip_address=public_ip_address,
            private_ip_address=private_ip_address,
            # TODO this does depend on distro... not root!
            # store this.
            default_user='root',
            ssh_key_path=ssh_key_path,
            default_transport=self._transport,
        )

    @property
    def masters(self) -> Set[Container]:
        """
        Docker containers which represent master nodes.
        """
        return self._instances_by_role(role=Role.MASTER)

    @property
    def agents(self) -> Set[Container]:
        """
        Docker containers which represent agent nodes.
        """
        return self._instances_by_role(role=Role.AGENT)

    @property
    def public_agents(self) -> Set[Container]:
        """
        Docker containers which represent public agent nodes.
        """
        return self._instances_by_role(role=Role.PUBLIC_AGENT)

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
