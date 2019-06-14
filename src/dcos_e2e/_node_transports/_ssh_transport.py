"""
Utilities to connect to nodes with SSH.
"""

import subprocess
from ipaddress import IPv4Address
from pathlib import Path
from shlex import quote
from typing import Any, Dict, List

import paramiko

from dcos_e2e._node_transports._base_classes import NodeTransport
from dcos_e2e._subprocess_tools import run_subprocess


def _compose_ssh_command(
    args: List[str],
    user: str,
    env: Dict[str, Any],
    tty: bool,
    ssh_key_path: Path,
    public_ip_address: IPv4Address,
) -> List[str]:
    """
    Return a command to run ``args`` on a node over SSH.

    Args:
        args: The command to run on a node.
        user: The user that the command will be run for over SSH.
        env: Environment variables to be set on the node before running
            the command. A mapping of environment variable names to
            values.
        tty: If ``True``, allocate a pseudo-tty. This means that the users
            terminal is attached to the streams of the process.
        public_ip_address: The public IP address of the node.
        ssh_key_path: The path to an SSH key which can be used to SSH to
            the node as the ``user`` user.

    Returns:
        The full SSH command to be run.
    """
    ssh_args = ['ssh']

    if tty:
        ssh_args.append('-t')

    ssh_args += [
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
        str(ssh_key_path),
        # Run commands as the specified user.
        '-l',
        user,
        # Bypass password checking.
        '-o',
        'PreferredAuthentications=publickey',
        # Do not add this node to the standard known hosts file.
        '-o',
        'UserKnownHostsFile=/dev/null',
        # Ignore warnings about remote host identification changes and new
        # hosts being added to the known hosts file in particular.
        # Also ignore "Connection to <IP-ADDRESS> closed".
        '-o',
        'LogLevel=QUIET',
        str(public_ip_address),
    ] + [
        '{key}={value}'.format(key=k, value=quote(str(v)))
        for k, v in env.items()
    ] + [quote(arg) for arg in args]

    return ssh_args


class SSHTransport(NodeTransport):
    """
    An SSH transport for nodes.
    """

    def run(
        self,
        args: List[str],
        user: str,
        log_output_live: bool,
        env: Dict[str, Any],
        tty: bool,
        ssh_key_path: Path,
        public_ip_address: IPv4Address,
        capture_output: bool,
    ) -> subprocess.CompletedProcess:
        """
        Run a command on this node the given user.

        Args:
            args: The command to run on the node.
            user: The username to communicate as.
            log_output_live: If ``True``, log output live. If ``True``, stderr
                is merged into stdout in the return value.
            env: Environment variables to be set on the node before running
                the command. A mapping of environment variable names to
                values.
            tty: If ``True``, allocate a pseudo-tty. This means that the users
                terminal is attached to the streams of the process.
                This means that the values of stdout and stderr will not be in
                the returned ``subprocess.CompletedProcess``.
            ssh_key_path: The path to an SSH key which can be used to SSH to
                the node as the ``user`` user.
            public_ip_address: The public IP address of the node.
            capture_output: Whether to capture output in the result.

        Returns:
            The representation of the finished process.

        Raises:
            subprocess.CalledProcessError: The process exited with a non-zero
                code.
        """
        ssh_args = _compose_ssh_command(
            args=args,
            user=user,
            env=env,
            tty=tty,
            ssh_key_path=ssh_key_path,
            public_ip_address=public_ip_address,
        )

        return run_subprocess(
            args=ssh_args,
            log_output_live=log_output_live,
            pipe_output=capture_output,
        )

    def popen(
        self,
        args: List[str],
        user: str,
        env: Dict[str, Any],
        ssh_key_path: Path,
        public_ip_address: IPv4Address,
    ) -> subprocess.Popen:
        """
        Open a pipe to a command run on a node as the given user.

        Args:
            args: The command to run on the node.
            user: The user to open a pipe for a command for over.
            env: Environment variables to be set on the node before running
                the command. A mapping of environment variable names to values.
            ssh_key_path: The path to an SSH key which can be used to SSH to
                the node as the ``user`` user.
            public_ip_address: The public IP address of the node.

        Returns:
            The pipe object attached to the specified process.
        """
        ssh_args = _compose_ssh_command(
            args=args,
            user=user,
            env=env,
            tty=False,
            ssh_key_path=ssh_key_path,
            public_ip_address=public_ip_address,
        )
        return subprocess.Popen(
            args=ssh_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def send_file(
        self,
        local_path: Path,
        remote_path: Path,
        user: str,
        ssh_key_path: Path,
        public_ip_address: IPv4Address,
    ) -> None:
        """
        Copy a file to this node.

        Args:
            local_path: The path on the host of the file to send.
            remote_path: The path on the node to place the file.
            user: The name of the remote user to send the file.
            ssh_key_path: The path to an SSH key which can be used to SSH to
                the node as the ``user`` user.
            public_ip_address: The public IP address of the node.
        """
        with paramiko.SSHClient() as ssh_client:
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(
                str(public_ip_address),
                username=user,
                key_filename=str(ssh_key_path),
            )

            with ssh_client.open_sftp() as sftp:
                sftp.put(
                    localpath=str(local_path),
                    remotepath=str(remote_path),
                )

    def download_file(
        self,
        remote_path: Path,
        local_path: Path,
        user: str,
        ssh_key_path: Path,
        public_ip_address: IPv4Address,
    ) -> None:
        """
        Download a file from this node.

        Args:
            remote_path: The path on the node to download the file from.
            local_path: The path on the host to download the file to.
            user: The name of the remote user to send the file.
            ssh_key_path: The path to an SSH key which can be used to SSH to
                the node as the ``user`` user.
            public_ip_address: The public IP address of the node.
        """
        with paramiko.SSHClient() as ssh_client:
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(
                str(public_ip_address),
                username=user,
                key_filename=str(ssh_key_path),
            )

            with ssh_client.open_sftp() as sftp:
                sftp.get(
                    remotepath=str(remote_path),
                    localpath=str(local_path),
                )
