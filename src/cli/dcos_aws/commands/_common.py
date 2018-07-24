"""
Common code for dcos-docker CLI modules.
"""

from typing import Set

import boto3

CLUSTER_ID_TAG_KEY = 'dcos_e2e.cluster_id'
NODE_TYPE_TAG_KEY = 'dcos_e2e.node_type'
NODE_TYPE_MASTER_TAG_VALUE = 'master'
NODE_TYPE_AGENT_TAG_VALUE = 'agent'
NODE_TYPE_PUBLIC_AGENT_TAG_VALUE = 'public_agent'
SSH_USER_TAG_KEY = 'dcos_e2e.ssh_user'
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
