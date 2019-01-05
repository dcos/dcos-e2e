"""
Common code for minidcos aws CLI modules.
"""

from pathlib import Path
from typing import Dict, Set

import boto3
from boto3.resources.base import ServiceResource

from dcos_e2e.cluster import Cluster
from dcos_e2e.distributions import Distribution
from dcos_e2e.node import Node, Role
from dcos_e2e_cli._vendor.dcos_installer_tools import DCOSVariant

CLUSTER_ID_TAG_KEY = 'dcos_e2e.cluster_id'
KEY_NAME_TAG_KEY = 'dcos_e2e.key_name'
LINUX_DISTRIBUTIONS = {
    'centos-7': Distribution.CENTOS_7,
    'rhel-7': Distribution.RHEL_7,
    'coreos': Distribution.COREOS,
}
NODE_TYPE_TAG_KEY = 'dcos_e2e.node_type'
NODE_TYPE_MASTER_TAG_VALUE = 'master'
NODE_TYPE_AGENT_TAG_VALUE = 'agent'
NODE_TYPE_PUBLIC_AGENT_TAG_VALUE = 'public_agent'
SSH_USER_TAG_KEY = 'dcos_e2e.ssh_user'
VARIANT_TAG_KEY = 'dcos_e2e.variant'
VARIANT_OSS_TAG_VALUE = ''
VARIANT_ENTERPRISE_TAG_VALUE = 'ee'
WORKSPACE_DIR_TAG_KEY = 'dcos_e2e.workspace_dir'


def _tag_dict(instance: ServiceResource) -> Dict[str, str]:
    """
    Return an EC2 instance's tags as a dictionary.
    """
    tag_dict = dict()  # type: Dict[str, str]

    if instance.tags is None:
        return tag_dict

    for tag in instance.tags:
        key = tag['Key']
        value = tag['Value']
        tag_dict[key] = value

    return tag_dict


def existing_cluster_ids(aws_region: str) -> Set[str]:
    """
    Return the IDs of existing clusters.

    Args:
        aws_region: The region to get clusters from.
    """
    ec2 = boto3.resource('ec2', region_name=aws_region)
    ec2_filter = {'Name': 'tag:' + CLUSTER_ID_TAG_KEY, 'Values': ['*']}
    ec2_instances = ec2.instances.filter(Filters=[ec2_filter])

    cluster_ids = set()  # type: Set[str]
    for instance in ec2_instances:
        tag_dict = _tag_dict(instance=instance)
        cluster_ids.add(tag_dict[CLUSTER_ID_TAG_KEY])

    return cluster_ids


class InstanceInspectView:
    """
    Details of a node from an instance.
    """

    def __init__(
        self,
        instance: ServiceResource,
        aws_region: str,
    ) -> None:
        """
        Args:
            instance: The EC2 instance which represents the node.
            aws_region: The AWS region the instance is on.
        """
        self._instance = instance
        self._aws_region = aws_region

    def to_dict(self) -> Dict[str, str]:
        """
        Return dictionary with information to be shown to users.
        """
        instance = self._instance
        tag_dict = _tag_dict(instance=instance)
        default_user = tag_dict[SSH_USER_TAG_KEY]
        cluster_id = tag_dict[CLUSTER_ID_TAG_KEY]
        role = tag_dict[NODE_TYPE_TAG_KEY]
        public_ip_address = instance.public_ip_address
        private_ip_address = instance.private_ip_address
        cluster_instances = ClusterInstances(
            cluster_id=cluster_id,
            aws_region=self._aws_region,
        )

        instances = {
            NODE_TYPE_MASTER_TAG_VALUE: cluster_instances.masters,
            NODE_TYPE_AGENT_TAG_VALUE: cluster_instances.agents,
            NODE_TYPE_PUBLIC_AGENT_TAG_VALUE: cluster_instances.public_agents,
        }[role]

        sorted_ips = sorted(
            [instance.public_ip_address for instance in instances],
        )

        index = sorted_ips.index(public_ip_address)

        return {
            'e2e_reference': '{role}_{index}'.format(role=role, index=index),
            'ec2_instance_id': instance.id,
            'public_ip_address': public_ip_address,
            'private_ip_address': private_ip_address,
            'aws_region': self._aws_region,
            'ssh_key': str(cluster_instances.workspace_dir / 'ssh' / 'id_rsa'),
            'ssh_user': default_user,
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
        node_types = {
            Role.MASTER: NODE_TYPE_MASTER_TAG_VALUE,
            Role.AGENT: NODE_TYPE_AGENT_TAG_VALUE,
            Role.PUBLIC_AGENT: NODE_TYPE_PUBLIC_AGENT_TAG_VALUE,
        }
        cluster_id_tag_filter = {
            'Name': 'tag:' + CLUSTER_ID_TAG_KEY,
            'Values': [self._cluster_id],
        }
        node_role_filter = {
            'Name': 'tag:' + NODE_TYPE_TAG_KEY,
            'Values': [node_types[role]],
        }
        filters = [cluster_id_tag_filter, node_role_filter]
        ec2_instances = set(ec2.instances.filter(Filters=filters))
        return ec2_instances

    def to_node(self, instance: ServiceResource) -> Node:
        """
        Return the ``Node`` that is represented by a given EC2 instance.
        """
        public_ip_address = instance.public_ip_address
        private_ip_address = instance.private_ip_address
        ssh_key_path = self.workspace_dir / 'ssh' / 'id_rsa'
        tag_dict = _tag_dict(instance=instance)
        default_user = tag_dict[SSH_USER_TAG_KEY]

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
        """
        The workspace directory to put temporary files in.
        """
        instance = next(iter(self.masters))
        tag_dict = _tag_dict(instance=instance)
        return Path(tag_dict[WORKSPACE_DIR_TAG_KEY])

    @property
    def dcos_variant(self) -> DCOSVariant:
        """
        Return the DC/OS variant of the cluster.
        """
        instance = next(iter(self.masters))
        tag_dict = _tag_dict(instance=instance)
        variant_tag_value = tag_dict[VARIANT_TAG_KEY]
        return {
            VARIANT_ENTERPRISE_TAG_VALUE: DCOSVariant.ENTERPRISE,
            VARIANT_OSS_TAG_VALUE: DCOSVariant.OSS,
        }[variant_tag_value]

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
