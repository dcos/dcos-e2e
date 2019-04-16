"""
Helpers for interacting with cluster nodes.
"""

from typing import Optional

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
