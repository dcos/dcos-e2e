"""
A CLI for controlling DC/OS clusters on AWS.
"""

import click

from .commands.create import create


@click.group(name='dcos-aws')
@click.version_option()
def dcos_aws() -> None:
    """
    Manage DC/OS clusters on AWS.
    """


dcos_aws.add_command(create)
