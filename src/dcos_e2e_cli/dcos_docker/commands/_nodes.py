"""
Helpers for interacting with specific nodes in a cluster.
"""

from typing import Callable, Optional

import click

from dcos_e2e.node import Node

from ._common import ClusterContainers, ContainerInspectView


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
            'The node\'s IP address, '
            'the node\'s Docker container name, '
            'the node\'s Docker container ID, '
            'a reference in the format "<role>_<number>". '
            'These details be seen with ``minidcos docker inspect``.'
        ),
    )(command)  # type: Callable[..., None]
    return function


def get_node(
    cluster_containers: ClusterContainers,
    node_reference: str,
) -> Optional[Node]:
    """
    Get a node from a "reference".

    Args:
        cluster_containers: A representation of the cluster.
        node_reference: One of:
            * A node's IP address
            * A node's Docker container name
            * A node's Docker container ID
            * A reference in the format "<role>_<number>"

    Returns:
        The ``Node`` from the given cluster or ``None`` if there is no such
        node.
    """
    containers = {
        *cluster_containers.masters,
        *cluster_containers.agents,
        *cluster_containers.public_agents,
    }

    for container in containers:
        inspect_view = ContainerInspectView(
            container=container,
            cluster_containers=cluster_containers,
        )
        inspect_data = inspect_view.to_dict()
        reference = inspect_data['e2e_reference']
        ip_address = inspect_data['ip_address']
        container_name = inspect_data['docker_container_name']
        container_id = inspect_data['docker_container_id']
        accepted = (
            reference,
            reference.upper(),
            ip_address,
            container_name,
            container_id,
        )

        if node_reference in accepted:
            return cluster_containers.to_node(container=container)
    return None


def get_nodes(
    node_references: Iterable[str],
    cluster_containers: ClusterContainers,
    inspect_command_name: str,
) -> Set[Node]:
    """
    Get nodes from "reference"s.
    Args:
        cluster_containers: A representation of the cluster.
        node_references: Each reference is one of:
            * A node's IP address
            * A node's Docker container name
            * A node's Docker container ID
            * A reference in the format "<role>_<number>"
        inspect_command_name: The name of an inspect command to use to find
            available references.

    Raises:
        click.BadParameter: There is no node which matches a given reference.
    """
    nodes = set([])
    for node_reference in node_references:
        node = get_node(
            cluster_containers=cluster_containers,
            node_reference=node_reference,
        )
        if node is None:
            message = (
                'No such node in cluster "{cluster_id}" with IP address, '
                'Docker container name, Docker container ID or node reference '
                '"{node_reference}". '
                'Node references can be seen with ``{inspect_command}``.'
            ).format(
                cluster_id=cluster_id,
                node_reference=node_reference,
                inspect_command=inspect_command_name,
            )
            raise click.BadParameter(message=message)

        nodes.add(host)
    return nodes
