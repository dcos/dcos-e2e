"""
Helpers for interacting with specific nodes in a cluster.
"""

from typing import Callable, Iterable, Optional, Set

import click

from dcos_e2e.node import Node

from ._common import ClusterInstances


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
) -> Optional[Node]:
    """
    Get a node from a "reference".

    Args:
        cluster_instances: A representation of the cluster.
        node_reference: One of:
            * A node's public IP address
            * A node's private IP address
            * A node's EC2 instance ID
            * A reference in the format "<role>_<number>"

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
        inspect_data = cluster_instances.to_dict(node_representation=instance)
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
            return cluster_instances.to_node(node_representation=instance)
    return None


def get_nodes(
    cluster_id: str,
    node_references: Iterable[str],
    cluster_instances: ClusterInstances,
    inspect_command_name: str,
) -> Set[Node]:
    """
    Get nodes from "reference"s.

    Args:
        cluster_id: The ID of the cluster to get nodes from.
        cluster_instances: A representation of the cluster.
        node_references: Each reference is one of:
            * A node's public IP address
            * A node's private IP address
            * A node's EC2 instance ID
            * A reference in the format "<role>_<number>"
        inspect_command_name: The name of an inspect command to use to find
            available references.

    Returns:
        All ``Node``s from the given cluster which match the references.

    Raises:
        click.BadParameter: There is no node which matches a given reference.
    """
    nodes = set([])
    for node_reference in node_references:
        node = get_node(
            cluster_instances=cluster_instances,
            node_reference=node_reference,
        )
        if node is None:
            message = (
                'No such node in cluster "{cluster_id}" with IP address, EC2 '
                'instance ID or node reference "{node_reference}". '
                'Node references can be seen with ``{inspect_command}``.'
            ).format(
                cluster_id=cluster_id,
                node_reference=node_reference,
                inspect_command=inspect_command_name,
            )
            raise click.BadParameter(message=message)

        nodes.add(node)
    return nodes
