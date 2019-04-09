"""
Helpers for installing DC/OS.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click

import dcos_e2e_cli.common.wait
from dcos_e2e.cluster import Cluster
from dcos_e2e_cli._vendor.dcos_installer_tools import DCOSVariant

from .credentials import DEFAULT_SUPERUSER_PASSWORD, DEFAULT_SUPERUSER_USERNAME


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


def run_post_install_steps(
    cluster: Cluster,
    cluster_id: str,
    dcos_config: Dict[str, Any],
    dcos_variant: DCOSVariant,
    doctor_command_name: str,
    http_checks: bool,
    wait_command_name: str,
    wait_for_dcos: bool,
) -> None:
    """
    Wait for DC/OS if wanted, else print a message stating that next you should
    wait.

    Args:
        cluster: A DC/OS cluster to run steps against.
        cluster_id: The ID of the cluster.
        dcos_config: The config that DC/OS was installed with.
        dcos_variant: The variant of DC/OS.
        doctor_command_name: The name of a ``doctor`` command to use if things
            go wrong.
        http_checks: Whether to run HTTP checks when waiting for DC/OS.
        wait_command_name: The name of a ``wait`` command to use after the
            cluster is installed.
        wait_for_dcos: Whether to wait for DC/OS to be installed.
    """
    superuser_username = dcos_config.get(
        'superuser_username',
        DEFAULT_SUPERUSER_USERNAME,
    )

    superuser_password = dcos_config.get(
        'superuser_password',
        DEFAULT_SUPERUSER_PASSWORD,
    )

    if wait_for_dcos:
        dcos_e2e_cli.common.wait.wait_for_dcos(
            dcos_variant=dcos_variant,
            cluster=cluster,
            superuser_username=superuser_username,
            superuser_password=superuser_password,
            http_checks=True,
            doctor_command_name=doctor_command_name,
        )

        return

    show_cluster_started_message(
        wait_command_name=wait_command_name,
        cluster_id=cluster_id,
    )

    click.echo(cluster_id)
