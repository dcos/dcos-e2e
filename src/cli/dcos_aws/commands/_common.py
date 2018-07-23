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
    ec2 = boto3.client('ec2', region_name=aws_region)
    # TODO fill this out
    return set()
