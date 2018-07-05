"""
Checks for showing up common sources of errors with the Vagrant backend.
"""

import sys

import click

from cli.common.doctor import CheckLevels, check_1_9_sed, check_ssh


def check_vagrant() -> CheckLevels:
    """
    Error if `vagrant` is not available on the path.
    """
    if shutil.which('vagrant') is None:
        error(message='`vagrant` must be available on the PATH.')
        return CheckLevels.ERROR
    return CheckLevels.NONE


@click.command('doctor')
def doctor() -> None:
    """
    Diagnose common issues which stop DC/OS E2E from working correctly.
    """
    check_functions = [
        check_1_9_sed,
        check_ssh,
        check_vagrant,
    ]

    highest_level = max(function() for function in check_functions)

    if highest_level == CheckLevels.ERROR:
        sys.exit(1)
