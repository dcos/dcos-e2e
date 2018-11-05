"""
Common utilities for making CLIs.
"""

import logging
import stat
import subprocess
import sys
from pathlib import Path
from shutil import rmtree
from typing import Set

import click
import click_spinner
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from cli._vendor.artifact_utils import get_dcos_installer_details


def get_variant(
    artifact_path: Path,
    doctor_message: str,
    workspace_dir: Path,
) -> str:
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
                build_artifact=artifact_path,
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
