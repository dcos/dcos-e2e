"""
Common helpers for doctor commands.
"""

import shutil
import subprocess
import sys
import tempfile
from enum import IntEnum
from pathlib import Path
from typing import Callable, List

import click
from tqdm import tqdm


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
    tqdm.write(s='')
    string = click.style('Note: ', fg='bright_green', bold=True) + message
    tqdm.write(s=string)


def warn(message: str) -> None:
    """
    Show a warning message.
    """
    tqdm.write(s='')
    string = click.style('Warning: ', fg='yellow', bold=True) + message
    tqdm.write(s=string)


def error(message: str) -> None:
    """
    Show an error message.
    """
    tqdm.write(s='')
    string = click.style('Error: ', fg='red', bold=True) + message
    tqdm.write(s=string)


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
            'http://minidcos.readthedocs.io/en/latest/versioning-and-api-stability.html#dc-os-1-9-and-below'  # noqa: E501
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


def run_doctor_commands(
    check_functions: List[Callable[[], CheckLevels]],
) -> None:
    """
    Run doctor commands.
    """
    progress_bar = tqdm(
        iterable=check_functions,
        dynamic_ncols=True,
        bar_format='{n_fmt}/{total_fmt} checks complete: {bar}',
        unit_scale=None,
    )

    for function in progress_bar:
        try:
            level = function()
        except Exception as exc:  # pylint: disable=broad-except
            message = (
                'There was an unknown error when performing a doctor '
                'check.\n'
                'The doctor function was "{doctor_function}".\n'
                'The error was: "{exception}".'
            ).format(
                doctor_function=function.__name__,
                exception=exc,
            )
            error(message=message)
            sys.exit(1)

        if level == CheckLevels.ERROR:
            sys.exit(1)


def get_doctor_message(doctor_command_name: str) -> str:
    """
    Return a message which instructs the user to use a given doctor command for
    troubleshooting help.

    Args:
        doctor_command_name: A command which will give troubleshooting help.
    """
    message = 'Try "' + doctor_command_name + '" for troubleshooting help.'
    return message
