"""
A CLI for controlling DC/OS clusters on AWS.
"""

import click

from .commands.create import create
from .commands.doctor import doctor
from .commands.inspect_cluster import inspect_cluster
from .commands.install_dcos import install_dcos
from .commands.list_clusters import list_clusters
from .commands.provision import provision
from .commands.run_command import run
from .commands.send_file import send_file
from .commands.sync import sync_code
from .commands.wait import wait
from .commands.web import web


@click.group(name='aws')
def dcos_aws() -> None:
    """
    Manage DC/OS clusters on AWS.
    """


dcos_aws.add_command(create)
dcos_aws.add_command(doctor)
dcos_aws.add_command(install_dcos)
dcos_aws.add_command(list_clusters)
dcos_aws.add_command(provision)
dcos_aws.add_command(run)
dcos_aws.add_command(send_file)
dcos_aws.add_command(sync_code)
dcos_aws.add_command(wait)
dcos_aws.add_command(web)
dcos_aws.add_command(inspect_cluster)
