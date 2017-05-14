"""
Common utilities for end to end tests.
"""

from ipaddress import IPv4Address
from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess, PIPE, Popen, STDOUT
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
        # return subprocess.run(
        #     args=ssh_args,
        #     check=True,
        #     stdout=subprocess.PIPE,
        #     stderr=subprocess.PIPE,
        # )


def run_subprocess(args: List[str],
                   cwd: Optional[Union[bytes, str]]=None) -> CompletedProcess:
    """
    XXX
    """

    with Popen(
        args=args,
        cwd=cwd,
        stdout=PIPE,
        stderr=STDOUT,
    ) as process:
        try:
            # Show live is an option
            for line in process.stdout:
                print(line)
            stdout, stderr = process.communicate()
        except:
            process.kill()
            process.wait()
            raise
        retcode = process.poll()
        if retcode:
            raise CalledProcessError(
                retcode, args, output=stdout, stderr=stderr
            )
    return CompletedProcess(args, retcode, stdout, stderr)
