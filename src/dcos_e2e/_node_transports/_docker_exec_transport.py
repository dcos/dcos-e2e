"""
Utilities to connect to nodes with Docker exec.
"""

import io
import subprocess
import tarfile
from ipaddress import IPv4Address
from pathlib import Path
from typing import Any, Dict, List

import docker

from dcos_e2e._common import get_logger
from dcos_e2e._node_transports._base_classes import NodeTransport
from ._docker_tools import container_exec

LOGGER = get_logger(__name__)

class DockerExecTransport(NodeTransport):
    """
    A Docker exec transport for nodes.
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

        Returns:
            The representation of the finished process.

        Raises:
            subprocess.CalledProcessError: The process exited with a non-zero
                code.
        """
        client = docker.from_env(version='auto')
        containers = client.containers.list()
        [container] = [
            container for container in containers
            if container.attrs['NetworkSettings']['IPAddress'] ==
            str(public_ip_address)
        ]

        result = container_exec(
            container=container,
            cmd=args,
            user=user,
            environment=env,
            stream=log_output_live,
            tty=tty,
        )

        stdout = b''
        stderr = b''

        # TODO figure out streamed output
        if log_output_live:
            # result.communicate()
            # TODO document this - None given for exit code with stream=True!
            # exit_code = 0
            for line in result.output:
                LOGGER.debug(
                    line.rstrip().decode('ascii', 'backslashreplace'),
                )
                stdout += line
            exit_code = result.communicate()
        else:
            exit_code = result.poll()
            stdout = result.output

        if exit_code != 0:
            raise subprocess.CalledProcessError(
                returncode=exit_code,
                cmd=args,
                output=stdout,
                stderr=b'',
            )

        return subprocess.CompletedProcess(
            args=args,
            returncode=exit_code,
            stdout=stdout,
            stderr=stderr,
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
        client = docker.from_env(version='auto')
        containers = client.containers.list()
        [container] = [
            container for container in containers
            if container.attrs['NetworkSettings']['IPAddress'] ==
            str(public_ip_address)
        ]

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
        client = docker.from_env(version='auto')
        containers = client.containers.list()
        [container] = [
            container for container in containers
            if container.attrs['NetworkSettings']['IPAddress'] ==
            str(public_ip_address)
        ]
        tarstream = io.BytesIO()
        with tarfile.TarFile(fileobj=tarstream, mode='w') as tar:
            tar.add(name=str(local_path), arcname='/' + remote_path.name)
        tarstream.seek(0)

        container.put_archive(path=str(remote_path.parent), data=tarstream)
