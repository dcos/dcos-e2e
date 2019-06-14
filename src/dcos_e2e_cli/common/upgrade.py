"""
Helpers for installing DC/OS.
"""

import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, Optional, Union

import click
from halo import Halo

from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Output

from .base_classes import ClusterRepresentation


def cluster_upgrade_dcos(
    cluster: Cluster,
    cluster_representation: ClusterRepresentation,
    ip_detect_path: Path,
    dcos_config: Dict[str, Any],
    local_genconf_dir: Optional[Path],
    dcos_installer: Union[Path, str],
    doctor_message: str,
    enable_spinner: bool,
) -> None:
    """
    Upgrade DC/OS on a cluster.

    Args:
        cluster: The cluster to upgrade DC/OS on.
        cluster_representation: A representation of the cluster.
        ip_detect_path: The ``ip-detect`` script to use for installing DC/OS.
        local_genconf_dir: A directory of files to copy from the host to the
            installer node before upgrading DC/OS.
        dcos_config: The DC/OS configuration to use.
        dcos_installer: The ``Path`` to a local DC/OS installer or a ``str``
            URL pointing to an installer.
        doctor_message: A message which instructs the user on which command to
            use if installation fails.
        enable_spinner: Whether to enable the spinner animation.
    """
    files_to_copy_to_genconf_dir = []
    if local_genconf_dir is not None:
        node_genconf_path = Path('/genconf')
        for genconf_file in local_genconf_dir.glob('*'):
            genconf_relative = genconf_file.relative_to(local_genconf_dir)
            relative_path = node_genconf_path / genconf_relative
            files_to_copy_to_genconf_dir.append((genconf_file, relative_path))

    spinner = Halo(enabled=enable_spinner)
    spinner.start('Upgrading DC/OS')

    try:
        cluster.upgrade_dcos(
            dcos_installer=dcos_installer,
            dcos_config=dcos_config,
            ip_detect_path=ip_detect_path,
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
            output=Output.LOG_AND_CAPTURE,
        )
    except subprocess.CalledProcessError as exc:
        spinner.stop()
        click.echo('Error upgrading DC/OS.', err=True)
        click.echo(click.style('Full error:', fg='yellow'))
        click.echo(click.style(textwrap.indent(str(exc), '  '), fg='yellow'))
        stderr = exc.stderr.decode()
        click.echo(click.style(textwrap.indent(stderr, '  '), fg='red'))
        click.echo(doctor_message)
        cluster_representation.destroy()
        sys.exit(exc.returncode)

    spinner.succeed()
