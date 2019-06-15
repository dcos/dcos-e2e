"""
Common code for minidcos aws CLI modules.
"""

from pathlib import Path
from typing import Any, Dict, Set

import boto3
from boto3.resources.base import ServiceResource

from dcos_e2e.backends import AWS
from dcos_e2e.cluster import Cluster
from dcos_e2e.distributions import Distribution
from dcos_e2e.node import Node, Role
from dcos_e2e_cli._vendor.dcos_launch import config, get_launcher
from dcos_e2e_cli.common.base_classes import ClusterRepresentation

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


class ClusterInstances(ClusterRepresentation):
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

    def _instances_by_role(self, role: Role) -> Set[ServiceResource]:
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

    def to_node(self, node_representation: ServiceResource) -> Node:
        """
        Return the ``Node`` that is represented by a given EC2 instance.
        """
        instance = node_representation
        public_ip_address = instance.public_ip_address
        private_ip_address = instance.private_ip_address

        return Node(
            public_ip_address=public_ip_address,
            private_ip_address=private_ip_address,
            default_user=self._ssh_default_user,
            ssh_key_path=self._ssh_key_path,
        )

    def to_dict(self, node_representation: ServiceResource) -> Dict[str, str]:
        """
        Return information to be shown to users which is unique to this node.
        """
        instance = node_representation
        tag_dict = _tag_dict(instance=instance)
        role = tag_dict[NODE_TYPE_TAG_KEY]
        public_ip_address = instance.public_ip_address
        private_ip_address = instance.private_ip_address

        instances = {
            NODE_TYPE_MASTER_TAG_VALUE: self.masters,
            NODE_TYPE_AGENT_TAG_VALUE: self.agents,
            NODE_TYPE_PUBLIC_AGENT_TAG_VALUE: self.public_agents,
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
            'ssh_user': self._ssh_default_user,
            'ssh_key': str(self._ssh_key_path),
        }

    @property
    def _ssh_default_user(self) -> str:
        """
        A user which can be used to SSH to any node using
        ``self.ssh_key_path``.
        """
        instance = next(iter(self.masters))
        tag_dict = _tag_dict(instance=instance)
        return tag_dict[SSH_USER_TAG_KEY]

    @property
    def _ssh_key_path(self) -> Path:
        """
        A key which can be used to SSH to any node.
        """
        return self._workspace_dir / 'ssh' / 'id_rsa'

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
    def _workspace_dir(self) -> Path:
        """
        The workspace directory to put temporary files in.
        """
        instance = next(iter(self.masters))
        tag_dict = _tag_dict(instance=instance)
        return Path(tag_dict[WORKSPACE_DIR_TAG_KEY])

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

    @property
    def base_config(self) -> Dict[str, Any]:
        """
        Return a base configuration for installing DC/OS OSS.
        """
        backend = AWS()

        return {
            **self.cluster.base_config,
            **backend.base_config,
        }

    def destroy(self) -> None:
        """
        Destroy this cluster.

        This is not yet implemented, see:
        https://jira.mesosphere.com/browse/DCOS_OSS-5042
        """
        cfr = boto3.resource('cloudformation', region_name='us-west-2')
        aws_distros = {
            Distribution.CENTOS_7: 'cent-os-7-dcos-prereqs',
            Distribution.COREOS: 'coreos',
            Distribution.RHEL_7: 'rhel-7-dcos-prereqs',
        }
        backend = AWS()
        deployment_name = self._cluster_id
        masters = len(self.masters)
        agents = len(self.agents)
        public_agents = len(self.public_agents)

        # Maybe not right
        aws_instance_type = backend.aws_instance_type

        launch_config = {
            'admin_location': backend.admin_location,
            'aws_region': self._aws_region,
            'deployment_name': deployment_name,
            # supply a valid url to the preliminary config.
            # this is replaced later before the dc/os installation.
            'installer_url': 'https://example.com',
            'instance_type': aws_instance_type,
            'launch_config_version': 1,
            'num_masters': masters,
            'num_private_agents': agents,
            'num_public_agents': public_agents,
            'os_name': aws_distros[backend.linux_distribution],
            'platform': 'aws',
            'provider': 'onprem',
            'install_prereqs': True,
            'prereqs_script_filename': 'centos',
        }

        launch_config['dcos_config'] = backend.base_config
        validated_launch_config = config.get_validated_config(
            user_config=launch_config,
            config_dir=str(self._workspace_dir),
        )
        cfr = boto3.resource('cloudformation', region_name='us-west-2')
        # import pdb; pdb.set_trace()
        filtered_stacks = cfr.stacks.filter(StackName=self._cluster_id).all()
        [stack] = list(filtered_stacks)
        stack_id = stack.stack_id
        # import pdb; pdb.set_trace()
        validated_launch_config['stack_id'] = stack_id
        launcher = get_launcher(config=validated_launch_config, )
        temp_resources = {}
        temp_resources.update(launcher.key_helper())
        temp_resources.update(launcher.zen_helper())
        validated_launch_config['temp_resources'] = temp_resources
        launcher.delete()
        import pdb
        pdb.set_trace()
