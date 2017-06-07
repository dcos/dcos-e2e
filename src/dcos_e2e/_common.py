"""
Common utilities for end to end tests.
"""

import logging
from ipaddress import IPv4Address
from pathlib import Path
from subprocess import (
    PIPE,
    STDOUT,
    CalledProcessError,
    CompletedProcess,
    Popen,
)
from typing import List, Optional, Union

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


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

    def run_as_root(self, args: List[str],
                    log_output_live: bool=False) -> CompletedProcess:
        """
        Run a command on this node as ``root``.

        Args:
            args: The command to run on the node.
            log_output_live: If `True`, log output live. If `True`, stderr is
                merged into stdout in the return value.

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

        return run_subprocess(args=ssh_args, log_output_live=log_output_live)


def run_subprocess(
    args: List[str],
    log_output_live: bool,
    cwd: Optional[Union[bytes, str]]=None
) -> CompletedProcess:
    """
    Run a command in a subprocess.

    Args:
        args: See `subprocess.run`.
        log_output_live: If `True`, log output live. If `True`, stderr is
            merged into stdout in the return value.
        cwd: See `subprocess.run`.

    Returns:
        See `subprocess.run`.

    Raises:
        CalledProcessError: See `subprocess.run`.
    """
    # It is hard to log output of both stdout and stderr live unless we
    # combine them.
    # See http://stackoverflow.com/a/18423003.
    if log_output_live:
        process_stderr = STDOUT
    else:
        process_stderr = PIPE

    with Popen(
        args=args,
        cwd=cwd,
        stdout=PIPE,
        stderr=process_stderr,
    ) as process:
        try:
            if log_output_live:
                stdout = b''
                stderr = b''
                for line in process.stdout:
                    LOGGER.debug(line)
                    stdout += line
                # Without this, `.poll()` will return None on some
                # systems.
                # See https://stackoverflow.com/a/33563376.
                process.communicate()
            else:
                stdout, stderr = process.communicate()
        except:
            process.kill()
            process.wait()
            raise
        retcode = process.poll()
        if retcode > 0:
            LOGGER.info(str(stderr))
            raise CalledProcessError(
                retcode, args, output=stdout, stderr=stderr
            )
    return CompletedProcess(args, retcode, stdout, stderr)
