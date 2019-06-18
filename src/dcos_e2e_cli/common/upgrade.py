"""
Helpers for installing DC/OS.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import click
from halo import Halo

from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Output

from .base_classes import ClusterRepresentation
from .error_handling import show_calledprocess_error


def cluster_upgrade_dcos_from_path(
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
    Upgrade DC/OS on a cluster.

    Args:
        cluster: The cluster to upgrade DC/OS on.
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
    spinner.start('Upgrading DC/OS')

    try:
        cluster.upgrade_dcos_from_path(
            dcos_installer=dcos_installer,
            dcos_config=dcos_config,
            ip_detect_path=ip_detect_path,
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
            output=Output.LOG_AND_CAPTURE,
        )
    except subprocess.CalledProcessError as exc:
        spinner.stop()
        show_calledprocess_error(exc=exc)
        click.echo(doctor_message)
        cluster_representation.destroy()
        sys.exit(exc.returncode)

    spinner.succeed()


def cluster_upgrade_dcos_from_url(
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
    Upgrade DC/OS on a cluster.

    Args:
        cluster: The cluster to upgrade DC/OS on.
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
    spinner.start('Upgrading DC/OS')

    try:
        cluster.upgrade_dcos_from_url(
            dcos_installer=dcos_installer,
            dcos_config=dcos_config,
            ip_detect_path=ip_detect_path,
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
            output=Output.LOG_AND_CAPTURE,
        )
    except subprocess.CalledProcessError as exc:
        spinner.stop()
        show_calledprocess_error(exc=exc)
        click.echo(doctor_message)
        cluster_representation.destroy()
        sys.exit(exc.returncode)

    spinner.succeed()
