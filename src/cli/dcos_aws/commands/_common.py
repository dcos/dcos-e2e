"""
Common code for dcos-docker CLI modules.
"""

from typing import Set

import boto3

CLUSTER_ID_TAG_KEY = 'dcos_e2e.cluster_id'


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
