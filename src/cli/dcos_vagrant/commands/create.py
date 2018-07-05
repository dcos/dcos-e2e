"""
Tools for creating a DC/OS cluster.
"""

import sys
import tempfile
import uuid
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, Optional

import click
import click_spinner

from cli.common.options import (
    agents_option,
    artifact_argument,
    extra_config_option,
    masters_option,
    public_agents_option,
    workspace_dir_option,
)
from dcos_e2e.backends import Vagrant
from dcos_e2e.cluster import Cluster


@click.command('create')
@artifact_argument
@masters_option
@agents_option
@extra_config_option
@public_agents_option
@workspace_dir_option
def create(
    agents: int,
    artifact: str,
    extra_config: Dict[str, Any],
    masters: int,
    public_agents: int,
    workspace_dir: Optional[Path],
) -> None:
    """
    Create an OSS DC/OS cluster.
    """
    base_workspace_dir = workspace_dir or Path(tempfile.gettempdir())
    workspace_dir = base_workspace_dir / uuid.uuid4().hex
    cluster_backend = Vagrant(workspace_dir=workspace_dir)
    doctor_message = 'Try `dcos-vagrant doctor` for troubleshooting help.'

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
        click.echo(doctor_message)
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
        click.echo(doctor_message)
        cluster.destroy()
        sys.exit(exc.returncode)
