"""
Helpers for installing DC/OS.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import click
from halo import Halo

import dcos_e2e_cli.common.wait
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Output

from .base_classes import ClusterRepresentation
from .credentials import DEFAULT_SUPERUSER_PASSWORD, DEFAULT_SUPERUSER_USERNAME
from .error_handling import show_calledprocess_error


def cluster_install_dcos_from_path(
    cluster: Cluster,
    cluster_representation: ClusterRepresentation,
    ip_detect_path: Path,
    dcos_config: Dict[str, Any],
    files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
    dcos_installer: Path,
    doctor_message: str,
    enable_spinner: bool,
) -> None:
    """
    Install DC/OS on a cluster.

    Args:
        cluster: The cluster to install DC/OS on.
        cluster_representation: A representation of the cluster.
        ip_detect_path: The ``ip-detect`` script to use for installing DC/OS.
        files_to_copy_to_genconf_dir: Pairs of host paths to paths on the
            installer node. These are files to copy from the host to the
            installer node before upgrading DC/OS.
        dcos_config: The DC/OS configuration to use.
        dcos_installer: The ``Path`` to a local DC/OS installer.
        doctor_message: A message which instructs the user on which command to
            use if installation fails.
        enable_spinner: Whether to enable the spinner animation.
    """
    spinner = Halo(enabled=enable_spinner)
    spinner.start('Installing DC/OS')

    # We allow a cluster to be passed in rather than just inferring it from
    # ``cluster_representation`` in case the ``cluster`` has a more efficient
    # installation method than a ``Cluster.from_nodes``.
    # However, if the cluster is a ``Cluster.from_nodes``, ``destroy`` will not
    # work and therefore we use ``cluster_representation.destroy`` instead.
    try:
        cluster.install_dcos_from_path(
            dcos_installer=dcos_installer,
            dcos_config=dcos_config,
            ip_detect_path=ip_detect_path,
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
            output=Output.LOG_AND_CAPTURE,
        )
    except subprocess.CalledProcessError as exc:
        spinner.stop()
        click.echo('Error installing DC/OS.', err=True)
        show_calledprocess_error(exc=exc)
        click.echo(doctor_message)
        cluster_representation.destroy()
        sys.exit(exc.returncode)

    spinner.succeed()


def cluster_install_dcos_from_url(
    cluster: Cluster,
    cluster_representation: ClusterRepresentation,
    ip_detect_path: Path,
    dcos_config: Dict[str, Any],
    files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
    dcos_installer: str,
    doctor_message: str,
    enable_spinner: bool,
) -> None:
    """
    Install DC/OS on a cluster.

    Args:
        cluster: The cluster to install DC/OS on.
        cluster_representation: A representation of the cluster.
        ip_detect_path: The ``ip-detect`` script to use for installing DC/OS.
        files_to_copy_to_genconf_dir: Pairs of host paths to paths on the
            installer node. These are files to copy from the host to the
            installer node before upgrading DC/OS.
        dcos_config: The DC/OS configuration to use.
        dcos_installer: A URL pointing to an installer.
        doctor_message: A message which instructs the user on which command to
            use if installation fails.
        enable_spinner: Whether to enable the spinner animation.
    """
    spinner = Halo(enabled=enable_spinner)
    spinner.start('Installing DC/OS')

    # We allow a cluster to be passed in rather than just inferring it from
    # ``cluster_representation`` in case the ``cluster`` has a more efficient
    # installation method than a ``Cluster.from_nodes``.
    # However, if the cluster is a ``Cluster.from_nodes``, ``destroy`` will not
    # work and therefore we use ``cluster_representation.destroy`` instead.
    try:
        cluster.install_dcos_from_url(
            dcos_installer=dcos_installer,
            dcos_config=dcos_config,
            ip_detect_path=ip_detect_path,
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
            output=Output.LOG_AND_CAPTURE,
        )
    except subprocess.CalledProcessError as exc:
        spinner.stop()
        click.echo('Error installing DC/OS.', err=True)
        show_calledprocess_error(exc=exc)
        click.echo(doctor_message)
        cluster_representation.destroy()
        sys.exit(exc.returncode)

    spinner.succeed()


def run_post_install_steps(
    cluster: Cluster,
    cluster_id: str,
    dcos_config: Dict[str, Any],
    doctor_command_name: str,
    http_checks: bool,
    wait_command_name: str,
    wait_for_dcos: bool,
    enable_spinner: bool,
) -> None:
    """
    Wait for DC/OS if wanted, else print a message stating that next you should
    wait.

    Args:
        cluster: A DC/OS cluster to run steps against.
        cluster_id: The ID of the cluster.
        dcos_config: The config that DC/OS was installed with.
        doctor_command_name: The name of a ``doctor`` command to use if things
            go wrong.
        http_checks: Whether to run HTTP checks when waiting for DC/OS.
        wait_command_name: The name of a ``wait`` command to use after the
            cluster is installed.
        wait_for_dcos: Whether to wait for DC/OS to be installed.
        enable_spinner: Whether to enable the spinner animation.
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
            cluster=cluster,
            superuser_username=superuser_username,
            superuser_password=superuser_password,
            http_checks=http_checks,
            doctor_command_name=doctor_command_name,
            enable_spinner=enable_spinner,
        )

        return

    cluster_started_message = (
        'Cluster "{cluster_id}" has started. '
        'Run "{wait_command_name} --cluster-id {cluster_id}" to wait for '
        'DC/OS to become ready.'
    ).format(
        cluster_id=cluster_id,
        wait_command_name=wait_command_name,
    )
    click.echo(cluster_started_message, err=True)

    click.echo(cluster_id)
