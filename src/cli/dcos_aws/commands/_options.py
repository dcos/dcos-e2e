"""
Common options for ``dcos-aws`` commands.
"""

from typing import Callable

import click


def aws_region_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for AWS regions.
    """
    function = click.option(
        '--aws-region',
        type=str,
        default='us-west-2',
        show_default=True,
        help='The AWS region to use.',
    )(command)  # type: Callable[..., None]
    return function
