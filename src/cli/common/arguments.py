"""
Click arguments which are common across CLI tools.
"""

from typing import Callable

import click


def dcos_checkout_dir_argument(command: Callable[..., None],
                               ) -> Callable[..., None]:
    """
    An argument decorator for choosing a DC/OS checkout directory.
    """
    function = click.argument(
        'dcos_checkout_dir',
        type=click.Path(exists=True),
        envvar='DCOS_CHECKOUT_DIR',
        default='.',
    )(command)  # type: Callable[..., None]
    return function
