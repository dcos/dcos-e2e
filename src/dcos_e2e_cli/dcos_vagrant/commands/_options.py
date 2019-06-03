"""
Common options for ``minidcos vagrant ``.
"""

from typing import Callable

import click

from dcos_e2e.backends import Vagrant


def vm_memory_mb_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for the amount of memory given to each VM.
    """
    backend = Vagrant()
    function = click.option(
        '--vm-memory-mb',
        type=click.INT,
        default=backend.vm_memory_mb,
        show_default=True,
        help='The amount of memory to give each VM.',
    )(command)  # type: Callable[..., None]
    return function
