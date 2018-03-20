"""
Tools for managing DC/OS cluster nodes.
"""

import stat
import subprocess
from datetime import datetime
from ipaddress import IPv4Address
from pathlib import Path
from shlex import quote
from typing import Any, Dict, List, Optional

import paramiko

from ._common import run_subprocess


class Node:
    """
    A record of a DC/OS cluster node.
    """

    def __init__(
        self,
        public_ip_address: IPv4Address,
        private_ip_address: IPv4Address,
        default_ssh_user: str,
        ssh_key_path: Path,
    ) -> None:
        """
        Args:
            public_ip_address: The public IP address of the node.
            private_ip_address: The IP address used by the DC/OS component
                running on this node.
            default_ssh_user: The default username to use for SSH connections.
            ssh_key_path: The path to an SSH key which can be used to SSH to
                the node as the ``default_ssh_user`` user.

        Attributes:
            ip_address: The IP address used by the DC/OS component
                running on this node.
        """
        self.public_ip_address = public_ip_address
        self.private_ip_address = private_ip_address
        self.default_ssh_user = default_ssh_user
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
        env: Optional[Dict[str, Any]],
        shell: bool,
        tty: bool,
        quiet: bool,
    ) -> List[str]:
        """
        Return a command to run `args` on this node over SSH.

        Args:
            args: The command to run on this node.
            user: The user that the command will be run for over SSH.
            env: Environment variables to be set on the node before running
                the command. A mapping of environment variable names to
                values.
            shell: If False, each argument is passed as a literal value to the
                command. If True, the command line is interpreted as a shell
                command, with a special meaning applied to some characters
                (e.g. $, &&, >). This means the caller must quote arguments if
                they may contain these special characters, including
                whitespace.
            tty: If ``True``, allocate a pseudo-tty. This means that the users
                terminal is attached to the streams of the process.
            quiet: Whether the SSH command is to be run in quiet mode.

        Returns:
            The full SSH command to be run.
        """
        env = dict(env or {})

        if shell:
            args = ['/bin/sh', '-c', ' '.join(args)]

        ssh_args = ['ssh']
        if tty:
            ssh_args.append('-t')

        if quiet:
            # Suppress warnings.
            # In particular, we often do not care about remote host
            # identification changes.
            ssh_args.append('-q')

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
            str(self._ssh_key_path),
            # Run commands as the specified user.
            '-l',
            user,
            # Bypass password checking.
            '-o',
            'PreferredAuthentications=publickey',
            str(self.public_ip_address),
        ] + [
            '{key}={value}'.format(key=k, value=quote(str(v)))
            for k, v in env.items()
        ] + [quote(arg) for arg in args]

        return ssh_args

    def run(
        self,
        args: List[str],
        user: Optional[str] = None,
        log_output_live: bool = False,
        env: Optional[Dict[str, Any]] = None,
        shell: bool = False,
        tty: bool = False,
        quiet: bool = True,
    ) -> subprocess.CompletedProcess:
        """
        Run a command on this node the given user.

        Args:
            args: The command to run on the node.
            user: The username to SSH as. If ``None`` then the
                ``default_ssh_user`` is used instead.
            log_output_live: If ``True``, log output live. If ``True``, stderr
                is merged into stdout in the return value.
            env: Environment variables to be set on the node before running
                the command. A mapping of environment variable names to
                values.
            shell: If ``False`` (the default), each argument is passed as a
                literal value to the command.  If True, the command line is
                interpreted as a shell command, with a special meaning applied
                to some characters (e.g. $, &&, >). This means the caller must
                quote arguments if they may contain these special characters,
                including whitespace.
            tty: If ``True``, allocate a pseudo-tty. This means that the users
                terminal is attached to the streams of the process.
                This means that the values of stdout and stderr will not be in
                the returned ``subprocess.CompletedProcess``.
            quiet: If ``False``, show SSH warnings.

        Returns:
            The representation of the finished process.

        Raises:
            subprocess.CalledProcessError: The process exited with a non-zero
                code.
        """
        if user is None:
            user = self.default_ssh_user

        ssh_args = self._compose_ssh_command(
            args=args,
            user=user,
            env=env,
            shell=shell,
            tty=tty,
            quiet=quiet,
        )

        return run_subprocess(
            args=ssh_args,
            log_output_live=log_output_live,
            pipe_output=not tty,
        )

    def popen(
        self,
        args: List[str],
        user: Optional[str] = None,
        env: Optional[Dict[str, Any]] = None,
        shell: bool = False,
    ) -> subprocess.Popen:
        """
        Open a pipe to a command run on a node as the given user.

        Args:
            args: The command to run on the node.
            user: The user to open a pipe for a command for over SSH.
                If `None` the ``default_ssh_user`` is used instead.
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
        if user is None:
            user = self.default_ssh_user

        ssh_args = self._compose_ssh_command(
            args=args,
            user=user,
            env=env,
            shell=shell,
            tty=False,
            quiet=True,
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
        user: Optional[str] = None,
    ) -> None:
        """
        Copy a file to this node.

        Args:
            local_path: The path on the host of the file to send.
            remote_path: The path on the node to place the file.
            user: The name of the remote user to send the file via
                secure copy. If `None` the ``default_ssh_user`` is
                used instead.
        """
        if user is None:
            user = self.default_ssh_user

        with paramiko.SSHClient() as ssh_client:
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(
                str(self.public_ip_address),
                username=user,
                key_filename=str(self._ssh_key_path),
            )

            self.run(
                args=['mkdir', '--parents',
                      str(remote_path.parent)],
                user=user,
            )

            with ssh_client.open_sftp() as sftp:
                sftp.put(
                    localpath=str(local_path),
                    remotepath=str(remote_path),
                )

    def dump_output(
        self,
        args: List[str],
        path: Path,
        user: Optional[str] = None,
        env: Optional[Dict[str, Any]] = None,
        shell: bool = False,
    ) -> None:
        """
        Dump the output of a particular SSH command composed of ``args``
        to a file in ``path`` with a filename like so:
        ``{private_ip}_{public_ip}_{args}_{datetime}.log``
        """
        if user is None:
            user = self.default_ssh_user

        result = self.run(
            args=args,
            user=user,
            env=env,
            shell=shell,
        )

        filename = '{private_ip}_{public_ip}_{command}_{datetime}.log'.format(
            private_ip=str(self.private_ip_address),
            public_ip=str(self.public_ip_address),
            command='_'.join(args),
            datetime=datetime.now().isoformat().split('.')[0],
        )

        filepath = Path(path / filename)

        with open(filepath, 'wb') as dumpfile:
            dumpfile.write(result.stdout)
