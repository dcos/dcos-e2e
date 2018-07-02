"""
Tools for creating a DC/OS cluster.
"""

import sys
from subprocess import CalledProcessError

import click

from dcos_e2e.backends import Vagrant
from dcos_e2e.cluster import Cluster


@click.command('create')
@click.argument('artifact', type=click.Path(exists=True))
@click.pass_context
def create(
    ctx: click.core.Context,
    artifact: str,
) -> None:
    """
    Create a DC/OS cluster.
    """
    cluster_backend = Vagrant()
    files_to_copy_to_installer = []
    masters = 1
    agents = 1
    public_agents = 1
    try:
        Cluster(
            cluster_backend=cluster_backend,
            masters=masters,
            agents=agents,
            public_agents=public_agents,
            files_to_copy_to_installer=files_to_copy_to_installer,
        )
    except CalledProcessError as exc:
        click.echo('Error creating cluster.', err=True)
        sys.exit(exc.returncode)
