"""
A CLI for controlling DC/OS clusters on Docker.
"""

import click

from cli.common.commands import download_artifact

from .commands.create import create
from .commands.destroy import destroy, destroy_list
from .commands.doctor import doctor
from .commands.inspect_cluster import inspect_cluster
from .commands.list_clusters import list_clusters
from .commands.mac_network import destroy_mac_network, setup_mac_network
from .commands.run_command import run
from .commands.sync import sync_code
from .commands.wait import wait
from .commands.web import web


@click.group(name='dcos-docker')
@click.version_option()
def dcos_docker() -> None:
    """
    Manage DC/OS clusters on Docker.
    """


dcos_docker.add_command(create)
dcos_docker.add_command(destroy)
dcos_docker.add_command(destroy_list)
dcos_docker.add_command(destroy_mac_network)
dcos_docker.add_command(doctor)
dcos_docker.add_command(download_artifact)
dcos_docker.add_command(inspect_cluster)
dcos_docker.add_command(list_clusters)
dcos_docker.add_command(run)
dcos_docker.add_command(setup_mac_network)
dcos_docker.add_command(sync_code)
dcos_docker.add_command(wait)
dcos_docker.add_command(web)
