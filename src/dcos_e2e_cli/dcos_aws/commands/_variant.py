"""
DC/OS Variant Option
"""

from typing import Callable

import click


def variant_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    Option to choose the DC/OS variant for installation.
    """
    function = click.option(
        '--variant',
        type=click.Choice(['oss', 'enterprise']),
        required=True,
        help=(
            'Choose the DC/OS variant. '
            'If the variant does not match the variant of the given installer '
            'URL, an error will occur. '
        ),
    )(command)  # type: Callable[..., None]
    return function
