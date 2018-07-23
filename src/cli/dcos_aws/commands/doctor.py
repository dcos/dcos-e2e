"""
Checks for showing up common sources of errors with the AWS backend.
"""

import click


@click.command('doctor')
def doctor() -> None:
    """
    Diagnose common issues which stop DC/OS E2E from working correctly.
    """
    # There are currently no doctor checks.
