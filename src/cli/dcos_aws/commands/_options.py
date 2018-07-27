"""
Common options for ``dcos-aws`` commands.
"""

from typing import Callable

import click

from ._common import LINUX_DISTRIBUTIONS


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


def linux_distribution_option(command: Callable[..., None],
                              ) -> Callable[..., None]:
    """
    An option decorator for choosing Linux distribution options on AWS.
    """
    function = click.option(
        '--linux-distribution',
        type=click.Choice(sorted(LINUX_DISTRIBUTIONS.keys())),
        default='centos-7',
        show_default=True,
        help='The Linux distribution to use on the nodes.',
    )(command)  # type: Callable[..., None]
    return function
