"""
Helpers for installing DC/OS.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import click

from dcos_e2e.cluster import Cluster


def install_dcos_from_path(
    cluster: Cluster,
    ip_detect_path: Path,
    dcos_config: Dict[str, Any],
    local_genconf_dir: Optional[Path],
    dcos_installer: Path,
    doctor_message: str,
) -> None:
    """
    Install DC/OS on a cluster from a path.

    Args:
        cluster: The cluster to install DC/OS on.
        ip_detect_path: The ``ip-detect`` script to use for installing DC/OS.
        local_genconf_dir: A directory of files to copy from the host to the
            installer node before installing DC/OS.
        dcos_config: The DC/OS configuration to use.
        dcos_installer: The path to a DC/OS installer.
        doctor_message: A message which instructs the user on which command to
            use if installation fails.
    """
    files_to_copy_to_genconf_dir = []
    if local_genconf_dir is not None:
        node_genconf_path = Path('/genconf')
        for genconf_file in local_genconf_dir.glob('*'):
            genconf_relative = genconf_file.relative_to(local_genconf_dir)
            relative_path = node_genconf_path / genconf_relative
            files_to_copy_to_genconf_dir.append((genconf_file, relative_path))

    try:
        cluster.install_dcos_from_path(
            dcos_installer=dcos_installer,
            dcos_config=dcos_config,
            ip_detect_path=ip_detect_path,
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
        )
    except subprocess.CalledProcessError as exc:
        click.echo('Error installing DC/OS.', err=True)
        click.echo(doctor_message)
        cluster.destroy()
        sys.exit(exc.returncode)


def install_dcos_from_url(
    cluster: Cluster,
    ip_detect_path: Path,
    dcos_config: Dict[str, Any],
    local_genconf_dir: Optional[Path],
    dcos_installer_url: str,
    doctor_message: str,
) -> None:
    """
    Install DC/OS on a cluster from a url.

    Args:
        cluster: The cluster to install DC/OS on.
        ip_detect_path: The ``ip-detect`` script to use for installing DC/OS.
        local_genconf_dir: A directory of files to copy from the host to the
            installer node before installing DC/OS.
        dcos_config: The DC/OS configuration to use.
        dcos_installer_url: A URL pointing to a DC/OS installer.
        doctor_message: A message which instructs the user on which command to
            use if installation fails.
    """
    files_to_copy_to_genconf_dir = []
    if local_genconf_dir is not None:
        node_genconf_path = Path('/genconf')
        for genconf_file in local_genconf_dir.glob('*'):
            genconf_relative = genconf_file.relative_to(local_genconf_dir)
            relative_path = node_genconf_path / genconf_relative
            files_to_copy_to_genconf_dir.append((genconf_file, relative_path))

    try:
        cluster.install_dcos_from_url(
            dcos_installer=dcos_installer_url,
            dcos_config=dcos_config,
            ip_detect_path=ip_detect_path,
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
        )
    except subprocess.CalledProcessError as exc:
        click.echo('Error installing DC/OS.', err=True)
        click.echo(doctor_message)
        cluster.destroy()
        sys.exit(exc.returncode)


def show_cluster_started_message(
    wait_command_name: str,
    cluster_id: str,
) -> None:
    """
    Show a message which says that the cluster has started.
    Point the user towards a ``wait`` command.

    Args:
        wait_command_name: A command which can take a ``--cluster-id`` option
            to wait for a cluster.
        cluster_id: The ID of a cluster which has just been created.
    """
    cluster_started_message = (
        'Cluster "{cluster_id}" has started. '
        'Run "{wait_command_name} --cluster-id {cluster_id}" to wait for '
        'DC/OS to become ready.'
    ).format(
        cluster_id=cluster_id,
        wait_command_name=wait_command_name,
    )
    click.echo(cluster_started_message, err=True)
