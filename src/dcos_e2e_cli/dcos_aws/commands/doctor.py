"""
Checks for showing up common sources of errors with the AWS backend.
"""

import click

from dcos_e2e_cli.common.doctor import check_ssh, run_doctor_commands
from dcos_e2e_cli.common.options import verbosity_option


@click.command('doctor')
@verbosity_option
def doctor() -> None:
    """
    Diagnose common issues which stop this CLI from working correctly.
    """
    check_functions = [check_ssh]
    run_doctor_commands(check_functions=check_functions)
