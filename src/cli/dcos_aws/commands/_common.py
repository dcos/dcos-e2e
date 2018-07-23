"""
Common code for dcos-docker CLI modules.
"""

from typing import Set

import boto3

CLUSTER_ID_TAG_KEY = 'dcos_e2e.cluster_id'

def existing_cluster_ids() -> Set[str]:
    """
    Return the IDs of existing clusters.
    """
    ec2 = boto3.client('ec2')

    # Retrieves all regions/endpoints that work with EC2
    response = ec2.describe_regions()
    print('Regions:', response['Regions'])
    # TODO fill this out
