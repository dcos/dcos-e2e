"""
Common utilities for making CLIs.
"""

import stat
from pathlib import Path
from typing import Set

import click
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


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
