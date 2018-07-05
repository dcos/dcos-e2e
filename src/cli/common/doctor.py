"""
Common helpers for doctor commands.
"""

import shutil
import subprocess
import tempfile
from enum import IntEnum
from pathlib import Path

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


def check_1_9_sed() -> CheckLevels:
    """
    Warn if the system's version of ``sed`` is incompatible with legacy DC/OS
    installers.
    """
    temp = tempfile.NamedTemporaryFile()
    Path(temp.name).write_text('a\na')
    sed_args = "sed '0,/a/ s/a/b/' " + temp.name
    result = subprocess.check_output(args=sed_args, shell=True)

    if result != b'b\na':
        message = (
            'The version of ``sed`` is not compatible with installers for '
            'DC/OS 1.9 and below. '
            'See '
            'http://dcos-e2e.readthedocs.io/en/latest/versioning-and-api-stability.html#dc-os-1-9-and-below'  # noqa: E501
            '.'
        )
        warn(message=message)
        return CheckLevels.WARNING

    return CheckLevels.NONE


def check_ssh() -> CheckLevels:
    """
    Error if `ssh` is not available on the path.
    """
    if shutil.which('ssh') is None:
        error(message='`ssh` must be available on the PATH.')
        return CheckLevels.ERROR
    return CheckLevels.NONE
