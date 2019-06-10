"""
A CLI for controlling DC/OS clusters on Vagrant.
"""

import click

from dcos_e2e_cli.common.commands import download_installer

from .commands.clean import clean
from .commands.create import create
from .commands.destroy import destroy, destroy_list
from .commands.doctor import doctor
from .commands.inspect_cluster import inspect_cluster
from .commands.install_dcos import install_dcos
from .commands.list_clusters import list_clusters
from .commands.provision import provision
from .commands.run_command import run
from .commands.send_file import send_file
from .commands.sync import sync_code
from .commands.upgrade import upgrade
from .commands.wait import wait
from .commands.web import web


@click.group(name='vagrant')
def dcos_vagrant() -> None:
    """
    Manage DC/OS clusters on Vagrant.
    """


dcos_vagrant.add_command(clean)
dcos_vagrant.add_command(create)
dcos_vagrant.add_command(destroy)
dcos_vagrant.add_command(destroy_list)
dcos_vagrant.add_command(doctor)
dcos_vagrant.add_command(download_installer)
dcos_vagrant.add_command(inspect_cluster)
dcos_vagrant.add_command(install_dcos)
dcos_vagrant.add_command(list_clusters)
dcos_vagrant.add_command(provision)
dcos_vagrant.add_command(run)
dcos_vagrant.add_command(send_file)
dcos_vagrant.add_command(sync_code)
dcos_vagrant.add_command(upgrade)
dcos_vagrant.add_command(wait)
dcos_vagrant.add_command(web)
