"""
Common options for ``minidcos aws`` commands.
"""

from typing import Callable

import click

from dcos_e2e.backends import AWS

from ._common import LINUX_DISTRIBUTIONS


def aws_instance_type_option(command: Callable[..., None],
                             ) -> Callable[..., None]:
    """
    An option decorator for AWS instance types.
    """
    default_instance_type = AWS().aws_instance_type
    function = click.option(
        '--aws-instance-type',
        type=str,
        default=default_instance_type,
        show_default=True,
        help='The AWS instance type to use.',
    )(command)  # type: Callable[..., None]
    return function


def aws_region_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for AWS regions.
    """
    default_region = AWS().aws_region

    function = click.option(
        '--aws-region',
        type=str,
        default=default_region,
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
