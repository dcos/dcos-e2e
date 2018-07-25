"""
Common code for dcos-aws CLI modules.
"""

from pathlib import Path
from typing import Set

import boto3
from boto3.resources.base import ServiceResource

from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node, Role

CLUSTER_ID_TAG_KEY = 'dcos_e2e.cluster_id'
KEY_NAME_TAG_KEY = 'dcos_e2e.key_name'
NODE_TYPE_TAG_KEY = 'dcos_e2e.node_type'
NODE_TYPE_MASTER_TAG_VALUE = 'master'
NODE_TYPE_AGENT_TAG_VALUE = 'agent'
NODE_TYPE_PUBLIC_AGENT_TAG_VALUE = 'public_agent'
SSH_USER_TAG_KEY = 'dcos_e2e.ssh_user'
VARIANT_TAG_KEY = 'dcos_e2e.variant'
WORKSPACE_DIR_TAG_KEY = 'dcos_e2e.workspace_dir'


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


class InstanceInspectView:
    """
    Details of a node from an instance.
    """

    def __init__(self, instance: ServiceResource) -> None:
        """
        Args:
            EC2 instance: The EC2 instance which represents the node.
        """
        self._instance = instance

    def to_dict(self) -> Dict[str, str]:
        """
        Return dictionary with information to be shown to users.
        """
        instance = self._instance
        role = instance.labels[NODE_TYPE_LABEL_KEY]
        instance_ip = instance.attrs['NetworkSettings']['IPAddress']
        cluster_instances = ClusterContainers(
            cluster_id=instance.labels[CLUSTER_ID_LABEL_KEY],
            transport=Transport.DOCKER_EXEC,
        )

        instances = {
            NODE_TYPE_MASTER_LABEL_VALUE: cluster_instances.masters,
            NODE_TYPE_AGENT_LABEL_VALUE: cluster_instances.agents,
            NODE_TYPE_PUBLIC_AGENT_LABEL_VALUE:
            cluster_instances.public_agents,
        }[role]

        sorted_ips = sorted(
            [ctr.attrs['NetworkSettings']['IPAddress'] for ctr in instances],
        )

        index = sorted_ips.index(instance_ip)

        return {
            'e2e_reference': '{role}_{index}'.format(role=role, index=index),
            'docker_EC2 instance_name': EC2 instance.name,
            'docker_EC2 instance_id': EC2 instance.id,
            'ip_address': EC2 instance_ip,
        }


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
        self._cluster_id = cluster_id
        self._aws_region = aws_region

    def _instances_by_role(
        self,
        role: Role,
    ) -> Set[ServiceResource]:
        """
        Return all EC2 instances in this cluster of a particular node type.
        """
        ec2 = boto3.resource('ec2', region_name=self._aws_region)
        ec2_instances = ec2.instances.all()

        cluster_instances = set([])
        for instance in ec2_instances:
            for tag in instance.tags:
                if tag['Key'] == CLUSTER_ID_TAG_KEY:
                    if tag['Value'] == self._cluster_id:
                        cluster_instances.add(instance)

        node_types = {
            Role.MASTER: NODE_TYPE_MASTER_TAG_VALUE,
            Role.AGENT: NODE_TYPE_AGENT_TAG_VALUE,
            Role.PUBLIC_AGENT: NODE_TYPE_PUBLIC_AGENT_TAG_VALUE,
        }
        role_instances = set([])
        for instance in cluster_instances:
            for tag in instance.tags:
                if tag['Key'] == NODE_TYPE_TAG_KEY:
                    if tag['Value'] == node_types[role]:
                        role_instances.add(instance)

        return role_instances

    def to_node(self, instance: ServiceResource) -> Node:
        """
        Return the ``Node`` that is represented by a given EC2 instance.
        """
        public_ip_address = instance.public_ip_address
        private_ip_address = instance.private_ip_address
        ssh_key_path = self.workspace_dir / 'ssh' / 'id_rsa'
        for tag in instance.tags:
            if tag['Key'] == SSH_USER_TAG_KEY:
                default_user = tag['Value']

        return Node(
            public_ip_address=public_ip_address,
            private_ip_address=private_ip_address,
            default_user=default_user,
            ssh_key_path=ssh_key_path,
        )

    @property
    def masters(self) -> Set[ServiceResource]:
        """
        EC2 instances which represent master nodes.
        """
        return self._instances_by_role(role=Role.MASTER)

    @property
    def agents(self) -> Set[ServiceResource]:
        """
        EC2 instances which represent agent nodes.
        """
        return self._instances_by_role(role=Role.AGENT)

    @property
    def public_agents(self) -> Set[ServiceResource]:
        """
        EC2 instances which represent public agent nodes.
        """
        return self._instances_by_role(role=Role.PUBLIC_AGENT)

    @property
    def workspace_dir(self) -> Path:
        instance = next(iter(self.masters))
        for tag in instance.tags:
            if tag['Key'] == WORKSPACE_DIR_TAG_KEY:
                workspace = Path(tag['Value'])
        return workspace

    @property
    def is_enterprise(self) -> bool:
        """
        Return whether the cluster is a DC/OS Enterprise cluster.
        """
        instance = next(iter(self.masters))
        for tag in instance.tags:
            if tag['Key'] == VARIANT_TAG_KEY:
                variant = Path(tag['Value'])
        return bool(variant == 'ee')

    @property
    def cluster(self) -> Cluster:
        """
        Return a ``Cluster`` constructed from the EC2 instances.
        """
        return Cluster.from_nodes(
            masters=set(map(self.to_node, self.masters)),
            agents=set(map(self.to_node, self.agents)),
            public_agents=set(map(self.to_node, self.public_agents)),
        )
