"""
Common code for dcos-docker CLI modules.
"""

from typing import Set

import boto3
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node

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

    def __init__(self, cluster_id: str) -> None:
        """
        Args:
            cluster_id: The ID of the cluster.
        """

    # def _containers_by_node_type(
    #     self,
    #     node_type: str,
    # ) -> Set[Container]:
    #     """
    #     Return all containers in this cluster of a particular node type.
    #     """
    #     client = docker_client()
    #     filters = {
    #         'label': [
    #             self._cluster_id_label,
    #             'node_type={node_type}'.format(node_type=node_type),
    #         ],
    #     }
    #     return set(client.containers.list(filters=filters))
    #
    # def to_node(self, container: Container) -> Node:
    #     """
    #     Return the ``Node`` that is represented by a given ``container``.
    #     """
    #     address = IPv4Address(container.attrs['NetworkSettings']['IPAddress'])
    #     ssh_key_path = self.workspace_dir / 'ssh' / 'id_rsa'
    #     return Node(
    #         public_ip_address=address,
    #         private_ip_address=address,
    #         default_user='root',
    #         ssh_key_path=ssh_key_path,
    #         default_transport=self._transport,
    #     )
    #
    # @property
    # def masters(self) -> Set[Container]:
    #     """
    #     EC2 instances which represent master nodes.
    #     """
    #     return self._containers_by_node_type(node_type='master')
    #
    # @property
    # def agents(self) -> Set[Container]:
    #     """
    #     EC2 instances which represent agent nodes.
    #     """
    #     return self._containers_by_node_type(node_type='agent')
    #
    # @property
    # def public_agents(self) -> Set[Container]:
    #     """
    #     EC2 instances which represent public agent nodes.
    #     """
    #     return self._containers_by_node_type(node_type='public_agent')
    #
    # @property
    # def cluster(self) -> Cluster:
    #     """
    #     Return a ``Cluster`` constructed from the containers.
    #     """
    #     return Cluster.from_nodes(
    #         masters=set(map(self.to_node, self.masters)),
    #         agents=set(map(self.to_node, self.agents)),
    #         public_agents=set(map(self.to_node, self.public_agents)),
    #         # Use a nonsense ``ip_detect_path`` since we never install DC/OS.
    #         ip_detect_path=Path('/foo'),
    #     )
