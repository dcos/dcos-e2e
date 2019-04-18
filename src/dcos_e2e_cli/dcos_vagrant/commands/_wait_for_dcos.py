"""
Wait for DC/OS readiness option
"""

from typing import Callable

import click


def wait_for_dcos_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    Option to choose waiting for DC/OS to be ready after starting the
    installation.
    """
    function = click.option(
        '--wait-for-dcos',
        is_flag=True,
        help=(
            'Wait for DC/OS after creating the cluster. '
            'This is equivalent to using "minidcos vagrant wait" after this '
            'command.'
        ),
    )(command)  # type: Callable[..., None]
    return function
