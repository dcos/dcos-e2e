"""
Helpers for interacting with specific nodes in a cluster.
"""

from typing import Callable

import click


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
            "The node's IP address, "
            "the node's VM name, "
            'a reference in the format "<role>_<number>". '
            'These details be seen with ``minidcos vagrant inspect``.'
        ),
    )(command)  # type: Callable[..., None]
    return function
