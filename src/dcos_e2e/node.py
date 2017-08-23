"""
Tools for managing DC/OS cluster nodes.
"""

from ipaddress import IPv4Address
from pathlib import Path
from subprocess import PIPE, CompletedProcess, Popen
from typing import Dict, List, Optional

from ._common import compose_ssh_command, run_subprocess


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
            ip_address: The IP address of the node.
        """
        self.ip_address = ip_address
        self._ssh_key_path = ssh_key_path

    def run_as_root(
        self,
        args: List[str],
        log_output_live: bool=False,
        env: Optional[Dict]=None,
    ) -> CompletedProcess:
        """
        Run a command on this node as `root`.

        Args:
            args: The command to run on the node.
            log_output_live: If `True`, log output live. If `True`, stderr is
                merged into stdout in the return value.
            env: Environment variables to be set on the node before running
                the command. A mapping of environment variable names to
                values.

        Returns:
            The representation of the finished process.

        Raises:
            CalledProcessError: The process exited with a non-zero code.
        """
        ssh_args = compose_ssh_command(
            self.ip_address, self._ssh_key_path, args, env
        )

        return run_subprocess(args=ssh_args, log_output_live=log_output_live)

    def popen_as_root(self, args: List[str],
                      env: Optional[Dict]=None) -> Popen:
        """
        Open a pipe to a command run on a node as `root`.

        Args:
            args: The command to run on the node.
            env: Environment variables to be set on the node before running
                the command. A mapping of environment variable names to
                values.

        Returns:
            The pipe object attached to the specified process.
        """
        ssh_args = compose_ssh_command(
            self.ip_address, self._ssh_key_path, args, env
        )

        process = Popen(args=ssh_args, stdout=PIPE, stderr=PIPE)

        return process
