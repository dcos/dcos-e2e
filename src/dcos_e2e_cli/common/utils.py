"""
Common utilities for making CLIs.
"""

import logging
import stat
import subprocess
import sys
from pathlib import Path
from shutil import rmtree
from typing import Optional, Set

import click
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from halo import Halo

from dcos_e2e_cli._vendor.dcos_installer_tools import (
    DCOSVariant,
    get_dcos_installer_details,
)


def command_path(
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
    given_variant: str,
    installer_path: Optional[Path],
    doctor_message: str,
    workspace_dir: Path,
) -> DCOSVariant:
    """
    Get the variant of DC/OS to install.

    Args:
        given_variant: The variant string given by the user to the
            ``variant_option``. One of "auto", "enterprise" and "oss". If
            "auto" is given, use the DC/OS installer to find the variant.
        installer_path: The path to a DC/OS installer, if available.
        workspace_dir: A directory to work in, given that this function uses
            large files.
        doctor_message: The message to show if something goes wrong.

    Returns:
        The variant of DC/OS to install.

    Raises:
        CalledProcessError: There was an error unpacking the installer.
    """
    if given_variant == 'auto':
        assert installer_path is not None
        try:
            with Halo(
                text='Determining DC/OS variant',
                enabled=sys.stdout.isatty(),
            ):
                return get_dcos_installer_details(
                    installer=installer_path,
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

    return {
        'oss': DCOSVariant.OSS,
        'enterprise': DCOSVariant.ENTERPRISE,
    }[given_variant]


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
