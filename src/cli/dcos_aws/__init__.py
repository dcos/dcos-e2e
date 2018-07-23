"""
A CLI for controlling DC/OS clusters on AWS.
"""

import click

from .commands.create import create
from .commands.doctor import doctor
from .commands.list_clusters import list_clusters


@click.group(name='dcos-aws')
@click.version_option()
def dcos_aws() -> None:
    """
    Manage DC/OS clusters on AWS.
    """


dcos_aws.add_command(create)
dcos_aws.add_command(doctor)
dcos_aws.add_command(list_clusters)
