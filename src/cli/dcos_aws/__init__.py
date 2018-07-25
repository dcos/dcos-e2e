"""
A CLI for controlling DC/OS clusters on AWS.
"""

import click

from .commands.create import create
from .commands.doctor import doctor
from .commands.list_clusters import list_clusters
from .commands.run_command import run
from .commands.sync import sync_code
from .commands.wait import wait


@click.group(name='dcos-aws')
@click.version_option()
def dcos_aws() -> None:
    """
    Manage DC/OS clusters on AWS.
    """


dcos_aws.add_command(create)
dcos_aws.add_command(doctor)
dcos_aws.add_command(list_clusters)
dcos_aws.add_command(run)
dcos_aws.add_command(sync_code)
dcos_aws.add_command(wait)
