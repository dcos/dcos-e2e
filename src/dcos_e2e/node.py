"""
Tools for managing DC/OS cluster nodes.
"""

from ipaddress import IPv4Address
from pathlib import Path
from subprocess import CompletedProcess
from typing import Dict, List, Optional

from ._common import run_subprocess


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

    def run(
        self,
        args: List[str],
        user: str,
        log_output_live: bool=False,
        env: Optional[Dict]=None,
    ) -> CompletedProcess:
        """
        Run a command on this node as a specific user.

        Args:
            args: The command to run on the node.
            user: The username to SSH as.
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
        env = dict(env or {})

        command = []

        for key, value in env.items():
            export = "export {key}='{value}'".format(key=key, value=value)
            command.append(export)
            command.append('&&')

        command += args

        ssh_args = [
            'ssh',
            # Suppress warnings.
            # In particular, we don't care about remote host identification
            # changes.
            '-q',
            # The node may be an unknown host.
            '-o',
            'StrictHostKeyChecking=no',
            # Use an SSH key which is authorized.
            '-i',
            str(self._ssh_key_path),
            # Run commands as the root user.
            '-l',
            user,
            # Bypass password checking.
            '-o',
            'PreferredAuthentications=publickey',
            str(self.ip_address),
        ] + command

        return run_subprocess(args=ssh_args, log_output_live=log_output_live)
