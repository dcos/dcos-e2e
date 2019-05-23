"""
Utilities to connect to nodes with Docker exec.
"""

import subprocess
import sys
from ipaddress import IPv4Address
from pathlib import Path
from typing import Any, Dict, List

import docker
from docker.models.containers import Container

from dcos_e2e._node_transports._base_classes import NodeTransport
from dcos_e2e._subprocess_tools import run_subprocess


def _compose_docker_command(
    args: List[str],
    user: str,
    env: Dict[str, Any],
    tty: bool,
    public_ip_address: IPv4Address,
) -> List[str]:
    """
    Return a command to run ``args`` on a node using ``docker exec``.

    We use this rather than using ``docker`` via Python for a few reasons.
    In particular, we would need something like ``dockerpty`` in order to
    support interaction.
    We also would need to match the ``Popen`` interface for asynchronous use.

    Args:
        args: The command to run on a node.
        user: The user that the command will be run for.
        env: Environment variables to be set on the node before running
            the command. A mapping of environment variable names to
            values.
        tty: If ``True``, allocate a pseudo-tty. This means that the users
            terminal is attached to the streams of the process.
        public_ip_address: The public IP address of the node.

    Returns:
        The full ``docker exec`` command to be run.
    """
    container = _container_from_ip_address(ip_address=public_ip_address)

    docker_exec_args = [
        'docker',
        'exec',
        '--user',
        user,
    ]

    # Do not cover this because there is currently no test for
    # using this in a terminal in the CI.
    if sys.stdin.isatty():  # pragma: no cover
        docker_exec_args.append('--interactive')

    if tty:
        docker_exec_args.append('--tty')

    for key, value in env.items():
        set_env = ['--env', '{key}={value}'.format(key=key, value=str(value))]
        docker_exec_args += set_env

    docker_exec_args.append(container.id)
    docker_exec_args += args

    return docker_exec_args


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
        docker_exec_args = _compose_docker_command(
            args=args,
            user=user,
            env=env,
            public_ip_address=public_ip_address,
            tty=tty,
        )

        return run_subprocess(
            args=docker_exec_args,
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
        docker_exec_args = _compose_docker_command(
            args=args,
            user=user,
            env=env,
            public_ip_address=public_ip_address,
            tty=False,
        )

        return subprocess.Popen(
            args=docker_exec_args,
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
        container = _container_from_ip_address(ip_address=public_ip_address)
        args = [
            'docker',
            'cp',
            str(local_path),
            container.id + ':' + str(remote_path),
        ]
        run_subprocess(
            args=args,
            log_output_live=False,
            pipe_output=True,
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
        container = _container_from_ip_address(ip_address=public_ip_address)
        args = [
            'docker',
            'cp',
            container.id + ':' + str(remote_path),
            str(local_path),
        ]
        run_subprocess(
            args=args,
            log_output_live=False,
            pipe_output=True,
        )


def _container_from_ip_address(ip_address: IPv4Address) -> Container:
    """
    Return the ``Container`` with the given ``ip_address``.
    """
    client = docker.from_env(version='auto')
    containers = client.containers.list()
    matching_containers = []
    for container in containers:
        networks = container.attrs['NetworkSettings']['Networks']
        for net in networks:
            if networks[net]['IPAddress'] == str(ip_address):
                matching_containers.append(container)

    assert len(matching_containers) == 1
    return matching_containers[0]
