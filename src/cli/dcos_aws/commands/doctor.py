"""
Checks for showing up common sources of errors with the AWS backend.
"""

import sys

import click

from cli.common.doctor import CheckLevels, check_ssh


@click.command('doctor')
def doctor() -> None:
    """
    Diagnose common issues which stop DC/OS E2E from working correctly.
    """
    check_functions = [check_ssh]
    for function in check_functions:
        level = function()
        if level == CheckLevels.ERROR:
            sys.exit(1)
