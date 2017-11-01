"""
Tools for managing DC/OS cluster nodes.
"""

from ipaddress import IPv4Address
from pathlib import Path
from subprocess import PIPE, CompletedProcess, Popen
from typing import Dict, List, Optional

import paramiko
from scp import SCPClient

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

    def _compose_ssh_command(
        self,
        args: List[str],
        user: str,
        env: Optional[Dict] = None,
    ) -> List[str]:
        """
        Return a command to run `args` on this node over SSH.

        Args:
            args: The command to run on this node.
            user: The user that the command will be run for over SSH.
            env: Environment variables to be set on the node before running
                the command. A mapping of environment variable names to
                values.

        Returns:
            The full SSH command to be run.
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
            # This makes sure that only keys passed with the -i option are
            # used. Needed when there are already keys present in the SSH
            # key chain, which cause `Error: Too many Authentication
            # Failures`.
            '-o',
            'IdentitiesOnly=yes',
            # The node may be an unknown host.
            '-o',
            'StrictHostKeyChecking=no',
            # Use an SSH key which is authorized.
            '-i',
            str(self._ssh_key_path),
            # Run commands as the specified user.
            '-l',
            user,
            # Bypass password checking.
            '-o',
            'PreferredAuthentications=publickey',
            str(self.ip_address),
        ] + command

        return ssh_args

    def run(
        self,
        args: List[str],
        user: str,
        log_output_live: bool = False,
        env: Optional[Dict] = None,
    ) -> CompletedProcess:
        """
        Run a command on this node the given user.

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
        ssh_args = self._compose_ssh_command(args=args, user=user, env=env)
        return run_subprocess(args=ssh_args, log_output_live=log_output_live)

    def run_as_root(
        self,
        args: List[str],
        log_output_live: bool = False,
        env: Optional[Dict] = None,
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

        return self.run(
            args=args,
            user='root',
            log_output_live=log_output_live,
            env=env,
        )

    def popen(
        self,
        args: List[str],
        user: str,
        env: Optional[Dict] = None,
    ) -> Popen:
        """
        Open a pipe to a command run on a node as the given user.

        Args:
            args: The command to run on the node.
            user: The user to open a pipe for a command for over SSH.
            env: Environment variables to be set on the node before running
                the command. A mapping of environment variable names to
                values.

        Returns:
            The pipe object attached to the specified process.
        """
        ssh_args = self._compose_ssh_command(args=args, user=user, env=env)
        return Popen(args=ssh_args, stdout=PIPE, stderr=PIPE)

    def send_file(self, local_path: Path, remote_path: Path) -> None:
        """
        Copy a file to this node.

        Args:
            local_path: The path on the host of the file to send.
            remote_path: The path on the node to place the file.
        """
        user = 'root'
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(
            str(self.ip_address),
            username=user,
            key_filename=str(self._ssh_key_path),
        )

        with SCPClient(ssh_client.get_transport()) as scp:
            scp.put(files=str(local_path), remote_path=str(remote_path))
