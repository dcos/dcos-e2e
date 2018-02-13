"""
Tools for managing DC/OS cluster nodes.
"""

import stat
from ipaddress import IPv4Address
from pathlib import Path
from shlex import quote
from subprocess import PIPE, CompletedProcess, Popen
from typing import Any, Dict, List, Optional

import paramiko
from scp import SCPClient

from ._common import run_subprocess


class Node:
    """
    A record of a DC/OS cluster node.
    """

    def __init__(
        self,
        public_ip_address: IPv4Address,
        private_ip_address: IPv4Address,
        ssh_key_path: Path,
    ) -> None:
        """
        Args:
            public_ip_address: The public IP address of the node.
            private_ip_address: The IP address used by the DC/OS component
                running on this node.
            ssh_key_path: The path to an SSH key which can be used to SSH to
                the node as the ``Cluster.default_ssh_user``.

        Attributes:
            ip_address: The IP address used by the DC/OS component
                running on this node.
        """
        self.public_ip_address = public_ip_address
        self.private_ip_address = private_ip_address
        ssh_key_path.chmod(mode=stat.S_IRUSR)
        self._ssh_key_path = ssh_key_path

    def __str__(self) -> str:
        """
        Convert a `Node` object to string listing only its IP addresses.

        Returns the custom string representation of a `Node` object.
        """
        return 'Node(public_ip={public_ip}, private_ip={private_ip})'.format(
            public_ip=self.public_ip_address,
            private_ip=self.private_ip_address,
        )

    def _compose_ssh_command(
        self,
        args: List[str],
        user: str,
        env: Optional[Dict[str, Any]] = None,
        shell: bool = False,
    ) -> List[str]:
        """
        Return a command to run `args` on this node over SSH.

        Args:
            args: The command to run on this node.
            user: The user that the command will be run for over SSH.
            env: Environment variables to be set on the node before running
                the command. A mapping of environment variable names to
                values.
            shell: If False (the default), each argument is passed as a
                literal value to the command.  If True, the command line is
                interpreted as a shell command, with a special meaning applied
                to some characters (e.g. $, &&, >). This means the caller must
                quote arguments if they may contain these special characters,
                including whitespace.

        Returns:
            The full SSH command to be run.
        """
        env = dict(env or {})

        if shell:
            args = ['/bin/sh', '-c', ' '.join(args)]

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
            str(self.public_ip_address),
        ] + [
            '{key}={value}'.format(key=k, value=quote(v))
            for k, v in env.items()
        ] + [quote(arg) for arg in args]

        return ssh_args

    def run(
        self,
        args: List[str],
        user: str,
        log_output_live: bool = False,
        env: Optional[Dict[str, Any]] = None,
        shell: bool = False,
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
            shell: If False (the default), each argument is passed as a
                literal value to the command.  If True, the command line is
                interpreted as a shell command, with a special meaning applied
                to some characters (e.g. $, &&, >). This means the caller must
                quote arguments if they may contain these special characters,
                including whitespace.

        Returns:
            The representation of the finished process.

        Raises:
            subprocess.CalledProcessError: The process exited with a non-zero
                code.
        """
        ssh_args = self._compose_ssh_command(
            args=args, user=user, env=env, shell=shell
        )
        return run_subprocess(args=ssh_args, log_output_live=log_output_live)

    def popen(
        self,
        args: List[str],
        user: str,
        env: Optional[Dict[str, Any]] = None,
        shell: bool = False,
    ) -> Popen:
        """
        Open a pipe to a command run on a node as the given user.

        Args:
            args: The command to run on the node.
            user: The user to open a pipe for a command for over SSH.
            env: Environment variables to be set on the node before running
                the command. A mapping of environment variable names to
                values.
            shell: If False (the default), each argument is passed as a
                literal value to the command.  If True, the command line is
                interpreted as a shell command, with a special meaning applied
                to some characters (e.g. $, &&, >). This means the caller must
                quote arguments if they may contain these special characters,
                including whitespace.

        Returns:
            The pipe object attached to the specified process.
        """
        ssh_args = self._compose_ssh_command(
            args=args, user=user, env=env, shell=shell
        )
        return Popen(args=ssh_args, stdout=PIPE, stderr=PIPE)

    def send_file(
        self,
        local_path: Path,
        remote_path: Path,
        user: str,
    ) -> None:
        """
        Copy a file to this node.

        Args:
            local_path: The path on the host of the file to send.
            remote_path: The path on the node to place the file.
            user: The name of the remote user to send the file via
                secure copy.
        """
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(
            str(self.public_ip_address),
            username=user,
            key_filename=str(self._ssh_key_path),
        )

        with SCPClient(ssh_client.get_transport()) as scp:
            self.run(
                args=['mkdir', '--parents',
                      str(remote_path.parent)],
                user=user,
            )
            scp.put(files=str(local_path), remote_path=str(remote_path))
