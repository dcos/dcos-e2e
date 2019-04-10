"""
Helpers for interacting with specific nodes in a cluster.
"""

from typing import Callable, Optional

import click

from dcos_e2e.node import Node

from ._common import ClusterInstances, InstanceInspectView


def node_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for choosing a node.
    """
    function = click.option(
        '--node',
        type=str,
        default=('master_0', ),
        show_default=True,
        multiple=True,
        help=(
            'A reference to a particular node to run the command on. '
            'This can be one of: '
            'The node\'s public IP address, '
            'The node\'s private IP address, '
            'the node\'s EC2 instance ID, '
            'a reference in the format "<role>_<number>". '
            'These details be seen with ``minidcos aws inspect``.'
        ),
    )(command)  # type: Callable[..., None]
    return function


def get_node(
    cluster_instances: ClusterInstances,
    node_reference: str,
    aws_region: str,
) -> Optional[Node]:
    """
    Get a node from a "reference".

    Args:
        cluster_vms: A representation of the cluster.
        node_reference: One of:
            * A node's public IP address
            * A node's private IP address
            * A node's EC2 instance ID
            * A reference in the format "<role>_<number>"
        aws_region: The AWS region the cluster is in.

    Returns:
        The ``Node`` from the given cluster or ``None`` if there is no such
        node.
    """
    instances = {
        *cluster_instances.masters,
        *cluster_instances.agents,
        *cluster_instances.public_agents,
    }

    for instance in instances:
        inspect_data = InstanceInspectView(
            instance=instance,
            aws_region=aws_region,
        ).to_dict()
        reference = inspect_data['e2e_reference']
        instance_id = inspect_data['ec2_instance_id']
        public_ip_address = inspect_data['public_ip_address']
        private_ip_address = inspect_data['private_ip_address']
        accepted = (
            reference,
            reference.upper(),
            instance_id,
            public_ip_address,
            private_ip_address,
        )

        if node_reference in accepted:
            return cluster_instances.to_node(instance=instance)
    return None
