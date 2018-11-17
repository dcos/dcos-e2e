"""
Common utilities for making CLIs.
"""

import logging
import stat
import subprocess
import sys
from pathlib import Path
from shutil import rmtree
from typing import Any, Dict, Iterable, Set, Tuple

import click
import click_spinner
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from dcos_e2e.cluster import Cluster
from dcos_e2e.exceptions import DCOSTimeoutError
from dcos_e2e_cli._vendor.dcos_installer_tools import (
    DCOSVariant,
    get_dcos_installer_details,
)


def _command_path(
    sibling_ctx: click.core.Context,
    command: click.core.Command,
) -> str:
    """
    Return the full path to a command, given the context of a sibling of the
    command.

    Args:
        sibling_ctx: A context associated with a call to a sibling of
            ``command``.
        command: A command.
    """
    command_path_list = sibling_ctx.command_path.split()
    command_path_list[-1] = command.name
    return ' '.join(command_path_list)


def get_variant(
    artifact_path: Path,
    doctor_message: str,
    workspace_dir: Path,
) -> DCOSVariant:
    """
    Get the variant of a DC/OS artifact.

    Args:
        artifact_path: The path to an artifact to get the DC/OS variant of.
        workspace_dir: A directory to work in, given that this function uses
            large files.
        doctor_message: The message to show if something goes wrong.

    Returns:
        "oss" or "enterprise" as appropriate.

    Raises:
        CalledProcessError: There was an error unpacking the artifact.
    """
    try:
        with click_spinner.spinner():
            return get_dcos_installer_details(
                installer=artifact_path,
                workspace_dir=workspace_dir,
            ).variant
    except subprocess.CalledProcessError as exc:
        rmtree(path=str(workspace_dir), ignore_errors=True)
        click.echo(doctor_message)
        click.echo()
        click.echo('Original error:', err=True)
        click.echo(exc.stderr, err=True)
        raise
    except ValueError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)


def set_logging(verbosity_level: int) -> None:
    """
    Set logging level depending on the chosen verbosity.
    """
    verbosity_level = min(verbosity_level, 3)
    verbosity_level = max(verbosity_level, 0)
    verbosity_map = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
        3: logging.NOTSET,
    }
    logging.basicConfig(level=logging.NOTSET)
    # Disable logging calls of the given severity level or below.
    logging.disable(verbosity_map[int(verbosity_level or 0)])


def check_cluster_id_unique(
    new_cluster_id: str,
    existing_cluster_ids: Set[str],
) -> None:
    """
    Raise an exception if a given Cluster ID already exists.
    """
    if new_cluster_id in existing_cluster_ids:
        message = 'A cluster with the id "{value}" already exists.'.format(
            value=new_cluster_id,
        )
        raise click.BadParameter(message=message)


def check_cluster_id_exists(
    new_cluster_id: str,
    existing_cluster_ids: Set[str],
) -> None:
    """
    Raise an exception if a given Cluster ID does not already exist.
    """
    if new_cluster_id not in existing_cluster_ids:
        message = 'Cluster "{value}" does not exist.'.format(
            value=new_cluster_id,
        )
        raise click.BadParameter(message)


def write_key_pair(public_key_path: Path, private_key_path: Path) -> None:
    """
    Write an RSA key pair for connecting to nodes via SSH.

    Args:
        public_key_path: Path to write public key to.
        private_key_path: Path to a private key file to write.
    """
    rsa_key_pair = rsa.generate_private_key(
        backend=default_backend(),
        public_exponent=65537,
        key_size=2048,
    )

    public_key = rsa_key_pair.public_key().public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH,
    )

    private_key = rsa_key_pair.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_key_path.write_bytes(data=public_key)
    private_key_path.write_bytes(data=private_key)

    private_key_path.chmod(mode=stat.S_IRUSR)


def show_wait_help(is_enterprise: bool, doctor_command_name: str) -> None:
    """
    Show a message useful for "wait" commands to warn the user of potential
    issues.

    Args:
        is_enterprise: Whether or not the cluster is a DC/OS Enterprise
            cluster.
        doctor_command_name: The full command path to a ``doctor`` command to
            advise a user to use.
    """
    message = (
        'A cluster may take some time to be ready.\n'
        'The amount of time it takes to start a cluster depends on a variety '
        'of factors.\n'
        'If you are concerned that this is hanging, try '
        '"{doctor_command_name}" to diagnose common issues.'
    ).format(doctor_command_name=doctor_command_name)
    click.echo(message)

    no_login_message = (
        'If you cancel this command while it is running, '
        'you may not be able to log in. '
        'To resolve that, run this command again.'
    )

    if not is_enterprise:
        click.echo(no_login_message)


def wait_for_dcos(
    is_enterprise: bool,
    cluster: Cluster,
    superuser_username: str,
    superuser_password: str,
    http_checks: bool,
) -> None:
    """
    Wait for DC/OS to start.

    Args:
        is_enterprise: Whether or not the cluster is a DC/OS Enterprise
            cluster.
        cluster: The cluster to wait for.
        superuser_username: If the cluster is a DC/OS Enterprise cluster, use
            this username to wait for DC/OS.
        superuser_password: If the cluster is a DC/OS Enterprise cluster, use
            this password to wait for DC/OS.
        http_checks: Whether or not to wait for checks which require an HTTP
            connection to the cluster.
    """
    with click_spinner.spinner():
        try:
            if is_enterprise:
                cluster.wait_for_dcos_ee(
                    superuser_username=superuser_username,
                    superuser_password=superuser_password,
                    http_checks=http_checks,
                )
                return

            cluster.wait_for_dcos_oss(http_checks=http_checks)
        except DCOSTimeoutError:
            click.echo('Waiting for DC/OS to start timed out.', err=True)
            sys.exit(1)


def install_dcos_from_path(
    cluster: Cluster,
    ip_detect_path: Path,
    dcos_config: Dict[str, Any],
    files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
    installer: Path,
    doctor_command: click.core.Command,
    sibling_ctx: click.core.Context,
) -> None:
    """
    Install DC/OS on a cluster.

    Args:
        cluster: The cluster to install DC/OS on.
        ip_detect_path: The ``ip-detect`` script to use for installing DC/OS.
        files_to_copy_to_genconf_dir: Pairs of host paths to paths on the
            installer node. These are files to copy from the host to the
            installer node before installing DC/OS.
        dcos_config: The DC/OS configuration to use.
        installer: The path to a DC/OS installer.
        doctor_command: A doctor command to suggest if the installation fails.
        sibling_ctx: A context associated with a call to a sibling of
            ``doctor_command``.
    """
    doctor_path = _command_path(
        sibling_ctx=sibling_ctx,
        command=doctor_command,
    )
    doctor_message = 'Try `{doctor_path}` for troubleshooting help.'.format(
        doctor_path=doctor_path,
    )
    try:
        with click_spinner.spinner():
            cluster.install_dcos_from_path(
                build_artifact=installer,
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
    sibling_ctx: click.core.Context,
    wait_command: click.core.Command,
    cluster_id: str,
) -> None:
    """
    Show a message which says that the cluster has started.
    Point the user towards a ``wait`` command.

    Args:
        sibling_ctx: A context associated with a call to a sibling of
            ``wait_command``.
        wait_command: A command which can take a ``--cluster-id`` option to
            wait for a cluster.
        cluster_id: The ID of a cluster which has just been created.
    """
    wait_command_name = _command_path(
        sibling_ctx=sibling_ctx,
        command=wait_command,
    )
    cluster_started_message = (
        'Cluster "{cluster_id}" has started. '
        'Run "{wait_command_name} --cluster-id {cluster_id}" to wait for '
        'DC/OS to become ready.'
    ).format(
        cluster_id=cluster_id,
        wait_command_name=wait_command_name,
    )
    click.echo(cluster_started_message, err=True)
