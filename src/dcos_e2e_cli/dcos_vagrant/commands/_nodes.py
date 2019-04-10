"""
Helpers for interacting with specific nodes in a cluster.
"""

from typing import Callable, Optional

import click

from dcos_e2e.node import Node

from ._common import ClusterVMs, VMInspectView


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
            'the node\'s VM name, '
            'a reference in the format "<role>_<number>". '
            'These details be seen with ``minidcos vagrant inspect``.'
        ),
    )(command)  # type: Callable[..., None]
    return function


def get_node(
    cluster_vms: ClusterVMs,
    node_reference: str,
) -> Optional[Node]:
    """
    Get a node from a "reference".

    Args:
        cluster_vms: A representation of the cluster.
        node_reference: One of:
            * A node's IP address
            * A node's VM name
            * A reference in the format "<role>_<number>"

    Returns:
        The ``Node`` from the given cluster or ``None`` if there is no such
        node.
    """
    vm_names = {
        *cluster_vms.masters,
        *cluster_vms.agents,
        *cluster_vms.public_agents,
    }

    for vm_name in vm_names:
        inspect_view = VMInspectView(vm_name=vm_name, cluster_vms=cluster_vms)
        inspect_data = inspect_view.to_dict()
        reference = inspect_data['e2e_reference']
        ip_address = inspect_data['ip_address']
        accepted = (
            reference,
            reference.upper(),
            ip_address,
            vm_name,
        )

        if node_reference in accepted:
            return cluster_vms.to_node(vm_name=vm_name)
    return None
