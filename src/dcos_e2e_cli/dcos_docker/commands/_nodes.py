"""
Helpers for interacting with specific nodes in a cluster.
"""

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
        The ``Node`` from the given cluster with the given ID or ``None`` if
        there is no such node.
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

