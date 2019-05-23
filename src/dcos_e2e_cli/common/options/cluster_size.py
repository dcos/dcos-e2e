"""
Options for choosing the cluster size.
"""

from typing import Callable

import click


def masters_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for the number of masters.
    """
    function = click.option(
        '--masters',
        type=click.INT,
        default=1,
        show_default=True,
        help='The number of master nodes.',
    )(command)  # type: Callable[..., None]
    return function


def agents_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for the number of agents.
    """
    function = click.option(
        '--agents',
        type=click.INT,
        default=1,
        show_default=True,
        help='The number of agent nodes.',
    )(command)  # type: Callable[..., None]
    return function


def public_agents_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for the number of agents.
    """
    function = click.option(
        '--public-agents',
        type=click.INT,
        default=1,
        show_default=True,
        help='The number of public agent nodes.',
    )(command)  # type: Callable[..., None]
    return function
