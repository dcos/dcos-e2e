"""
Tools for creating a DC/OS cluster.
"""

import sys
from pathlib import Path
from subprocess import CalledProcessError

import click
import click_spinner

from dcos_e2e.backends import Vagrant
from dcos_e2e.cluster import Cluster


@click.command('create')
@click.argument('artifact', type=click.Path(exists=True))
def create(artifact: str) -> None:
    """
    Create an OSS DC/OS cluster.
    """
    cluster_backend = Vagrant()
    masters = 1
    agents = 1
    public_agents = 1
    extra_config = {}

    artifact_path = Path(artifact).resolve()

    try:
        cluster = Cluster(
            cluster_backend=cluster_backend,
            masters=masters,
            agents=agents,
            public_agents=public_agents,
            files_to_copy_to_installer=[],
        )
    except CalledProcessError as exc:
        click.echo('Error creating cluster.', err=True)
        sys.exit(exc.returncode)

    try:
        with click_spinner.spinner():
            cluster.install_dcos_from_path(
                build_artifact=artifact_path,
                dcos_config={
                    **cluster.base_config,
                    **extra_config,
                },
            )
    except CalledProcessError as exc:
        click.echo('Error installing DC/OS.', err=True)
        cluster.destroy()
        sys.exit(exc.returncode)
