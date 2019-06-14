"""
A CLI for controlling DC/OS clusters on Docker.
"""

import click

from dcos_e2e_cli.common.commands import download_installer

from .commands.clean import clean
from .commands.create import create
from .commands.create_loopback_sidecar import create_loopback_sidecar
from .commands.destroy import destroy, destroy_list
from .commands.destroy_loopback_sidecar import destroy_loopback_sidecar
from .commands.doctor import doctor
from .commands.inspect_cluster import inspect_cluster
from .commands.install_dcos import install_dcos
from .commands.list_clusters import list_clusters
from .commands.list_loopback_sidecars import list_loopback_sidecars
from .commands.mac_network import destroy_mac_network, setup_mac_network
from .commands.provision import provision
from .commands.run_command import run
from .commands.send_file import send_file
from .commands.sync import sync_code
from .commands.upgrade import upgrade
from .commands.wait import wait
from .commands.web import web


@click.group(name='docker')
def dcos_docker() -> None:
    """
    Manage DC/OS clusters on Docker.
    """


dcos_docker.add_command(clean)
dcos_docker.add_command(create)
dcos_docker.add_command(create_loopback_sidecar)
dcos_docker.add_command(destroy)
dcos_docker.add_command(destroy_list)
dcos_docker.add_command(destroy_loopback_sidecar)
dcos_docker.add_command(destroy_mac_network)
dcos_docker.add_command(doctor)
dcos_docker.add_command(download_installer)
dcos_docker.add_command(inspect_cluster)
dcos_docker.add_command(install_dcos)
dcos_docker.add_command(list_clusters)
dcos_docker.add_command(list_loopback_sidecars)
dcos_docker.add_command(provision)
dcos_docker.add_command(run)
dcos_docker.add_command(setup_mac_network)
dcos_docker.add_command(send_file)
dcos_docker.add_command(sync_code)
dcos_docker.add_command(wait)
dcos_docker.add_command(web)
dcos_docker.add_command(upgrade)
