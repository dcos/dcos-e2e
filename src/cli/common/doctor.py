"""
Common helpers for doctor commands.
"""

from enum import IntEnum

import click


class CheckLevels(IntEnum):
    """
    Levels of issues that a check can raise.
    """

    NONE = 1
    WARNING = 2
    ERROR = 3


def info(message: str) -> None:
    """
    Show an info message.
    """
    click.echo()
    click.echo(click.style('Note: ', fg='blue'), nl=False)
    click.echo(message)


def warn(message: str) -> None:
    """
    Show a warning message.
    """
    click.echo()
    click.echo(click.style('Warning: ', fg='yellow'), nl=False)
    click.echo(message)


def error(message: str) -> None:
    """
    Show an error message.
    """
    click.echo()
    click.echo(click.style('Error: ', fg='red'), nl=False)
    click.echo(message)
