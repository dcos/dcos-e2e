"""
Helpers for interacting with cluster nodes.
"""

from typing import Iterable, Optional, Set

import click

from dcos_e2e.node import Node
from dcos_e2e_cli.common.base_classes import ClusterRepresentation


def get_node(
    cluster_representation: ClusterRepresentation,
    node_reference: str,
) -> Optional[Node]:
    """
    Get a node from a "reference".

    Args:
        cluster_representation: A representation of the cluster.
        node_reference: Unique node data as shown in the "inspect" command.

    Returns:
        The ``Node`` from the given cluster or ``None`` if there is no such
            node.
    """
    node_representations = {
        *cluster_representation.masters,
        *cluster_representation.agents,
        *cluster_representation.public_agents,
    }

    for node_representation in node_representations:
        inspect_data = cluster_representation.to_dict(
            node_representation=node_representation,
        )
        if node_reference in inspect_data.values():
            return cluster_representation.to_node(
                node_representation=node_representation,
            )
    return None


def get_nodes(
    cluster_id: str,
    node_references: Iterable[str],
    cluster_representation: ClusterRepresentation,
    inspect_command_name: str,
) -> Set[Node]:
    """
    Get nodes from "reference"s.

    Args:
        cluster_id: The ID of the cluster to get nodes from.
        cluster_representation: A representation of the cluster.
        node_references: Each reference is a unique node data as shown in the
            "inspect" command.
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
            cluster_representation=cluster_representation,
            node_reference=node_reference,
        )
        if node is None:
            message = (
                'No node in cluster "{cluster_id}" has the unique reference '
                '"{node_reference}". '
                'Node references can be seen with ``{inspect_command}``.'
            ).format(
                cluster_id=cluster_id,
                node_reference=node_reference,
                inspect_command=inspect_command_name,
            )
            raise click.BadParameter(message=message)

        nodes.add(node)
    return nodes
