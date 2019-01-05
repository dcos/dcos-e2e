"""
Checks for showing up common sources of errors with the AWS backend.
"""

import click

from dcos_e2e_cli.common.doctor import check_ssh, run_doctor_commands
from dcos_e2e_cli.common.options import verbosity_option
from dcos_e2e_cli.common.utils import set_logging


@click.command('doctor')
@verbosity_option
def doctor(verbose: int) -> None:
    """
    Diagnose common issues which stop this CLI from working correctly.
    """
    set_logging(verbosity_level=verbose)
    check_functions = [check_ssh]
    run_doctor_commands(check_functions=check_functions)
