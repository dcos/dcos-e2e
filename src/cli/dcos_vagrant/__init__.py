"""
A CLI for controlling DC/OS clusters on Vagrant.
"""

import click

from cli.common.commands import (
    download_artifact,
    list_clusters_command_factory,
)

from .commands._common import existing_cluster_ids
from .commands.create import create
from .commands.destroy import destroy, destroy_list
from .commands.doctor import doctor
from .commands.inspect_cluster import inspect_cluster
from .commands.run_command import run
from .commands.sync import sync_code
from .commands.wait import wait
from .commands.web import web


@click.group(name='dcos-vagrant')
@click.version_option()
def dcos_vagrant() -> None:
    """
    Manage DC/OS clusters on Vagrant.
    """


LIST_CLUSTERS = list_clusters_command_factory(
    existing_cluster_ids_func=existing_cluster_ids,
)
dcos_vagrant.add_command(create)
dcos_vagrant.add_command(destroy)
dcos_vagrant.add_command(destroy_list)
dcos_vagrant.add_command(doctor)
dcos_vagrant.add_command(download_artifact)
dcos_vagrant.add_command(inspect_cluster)
dcos_vagrant.add_command(LIST_CLUSTERS)
dcos_vagrant.add_command(run)
dcos_vagrant.add_command(sync_code)
dcos_vagrant.add_command(wait)
dcos_vagrant.add_command(web)
