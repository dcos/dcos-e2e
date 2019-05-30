"""
Common options for ``minidcos vagrant ``.
"""

from typing import Callable

import click


def vm_memory_mb_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for the amount of memory given to each VM.
    """
    function = click.option(
        '--vm-memory-mb',
        type=click.INT,
        default=2048,
        show_default=True,
        help='The amount of memory to give each VM.',
    )(command)  # type: Callable[..., None]
    return function
