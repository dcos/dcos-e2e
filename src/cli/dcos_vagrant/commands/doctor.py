"""
Checks for showing up common sources of errors with the Vagrant backend.
"""

import sys

import click

from cli.common.doctor import CheckLevels, check_1_9_sed, check_ssh


@click.command('doctor')
def doctor() -> None:
    """
    Diagnose common issues which stop DC/OS E2E from working correctly.
    """
    check_functions = [
        check_1_9_sed,
        check_ssh,
    ]

    highest_level = max(function() for function in check_functions)

    if highest_level == CheckLevels.ERROR:
        sys.exit(1)
