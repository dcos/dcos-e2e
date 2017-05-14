"""
Common utilities for end to end tests.
"""

from ipaddress import IPv4Address
from pathlib import Path
from subprocess import PIPE, CompletedProcess, run
from typing import List, Optional, Union


class Node:
    """
    A record of a DC/OS cluster node.
    """

    def __init__(self, ip_address: IPv4Address, ssh_key_path: Path) -> None:
        """
        Args:
            ip_address: The IP address of the node.
            ssh_key_path: The path to an SSH key which can be used to SSH to
                the node as the `root` user.

        Attributes:
            ip_address (IPv4Address): The IP address of the node.
        """
        self.ip_address = ip_address
        self._ssh_key_path = ssh_key_path

    def run_as_root(self, args: List[str]) -> CompletedProcess:
        """
        Run a command on this node as ``root``.

        Args:
            args: The command to run on the node.

        Returns:
            The representation of the finished process.

        Raises:
            CalledProcessError: The process exited with a non-zero code.
        """
        ssh_args = [
            'ssh',
            # Suppress warnings.
            # In particular, we don't care about remote host identification
            # changes.
            "-q",
            # The node may be an unknown host.
            "-o",
            "StrictHostKeyChecking=no",
            # Use an SSH key which is authorized.
            "-i",
            str(self._ssh_key_path),
            # Run commands as the root user.
            "-l",
            "root",
            # Bypass password checking.
            "-o",
            "PreferredAuthentications=publickey",
            str(self.ip_address),
        ] + args

        return run_subprocess(args=ssh_args)


def run_subprocess(args: List[str],
                   cwd: Optional[Union[bytes, str]]=None) -> CompletedProcess:
    """
    Run a command in a subprocess.

    Args:
        args: See `subprocess.run`.
        cwd: See `subprocess.run`.

    Returns:
        See `subprocess.run`.
    """
    return run(
        args=args,
        check=True,
        stdout=PIPE,
        stderr=PIPE,
    )
