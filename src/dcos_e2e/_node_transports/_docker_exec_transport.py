"""
Utilities to connect to nodes with Docker exec.
"""

import io
import os
import subprocess
import tarfile
import uuid
from ipaddress import IPv4Address, IPv6Address
from pathlib import Path
from typing import Any, Dict, List, Union

import docker

from dcos_e2e._common import get_logger, run_subprocess
from dcos_e2e._node_transports._base_classes import NodeTransport

LOGGER = get_logger(__name__)


def _compose_docker_command(
    args: List[str],
    user: str,
    env: Dict[str, Any],
    tty: bool,
    public_ip_address: IPv4Address,
) -> List[str]:
    """
    Return a command to run ``args`` on a node using ``docker exec``. We do not
    use ``docker-py`` because ``stdout`` and ``stderr`` cannot be separated in
    ``docker-py`` https://github.com/docker/docker-py/issues/704.

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
    container = _get_container_from_ip_address(public_ip_address)

    docker_exec_args = [
        'docker',
        'exec',
        '--user',
        user,
    ]

    if tty:
        docker_exec_args.append('--interactive')
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
            pipe_output=not tty,
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
        # `remote_path` may be a tmpfs mount.
        # At the time of writing, for example, `/tmp` is a tmpfs mount.
        # Copying files to tmpfs mounts fails silently.
        # See https://github.com/moby/moby/issues/22020.

        # Therefore, we create a temporary directory within our home directory,
        # and we put the file there.
        # We then move the file from the temporary directory to the intended
        # destination.
        # We then remove the temporary directory.

        home_path = self.run(
            args=['bash', '-c', 'echo $HOME'],
            user=user,
            log_output_live=False,
            env={},
            tty=False,
            ssh_key_path=ssh_key_path,
            public_ip_address=public_ip_address,
        ).stdout.strip().decode()

        tmp_path = '{home}/dcos-docker-{uuid}'.format(
            home=home_path,
            uuid=uuid.uuid4().hex,
        )

        self.run(
            args=['mkdir', tmp_path],
            user=user,
            log_output_live=False,
            env={},
            tty=False,
            ssh_key_path=ssh_key_path,
            public_ip_address=public_ip_address,
        )

        container = _get_container_from_ip_address(public_ip_address)
        tarstream = io.BytesIO()
        with tarfile.TarFile(fileobj=tarstream, mode='w') as tar:
            tar.add(name=str(local_path), arcname='/' + remote_path.name)
        tarstream.seek(0)

        container.put_archive(path=tmp_path, data=tarstream)
        self.run(
            args=[
                'mv',
                os.path.join(tmp_path, remote_path.name),
                str(remote_path.parent),
            ],
            user=user,
            log_output_live=False,
            env={},
            tty=False,
            ssh_key_path=ssh_key_path,
            public_ip_address=public_ip_address,
        )

        self.run(
            args=['rm', '-rf', tmp_path],
            user=user,
            log_output_live=False,
            env={},
            tty=False,
            ssh_key_path=ssh_key_path,
            public_ip_address=public_ip_address,
        )


def _get_container_from_ip_address(ip_addr: Union[IPv4Address, IPv6Address],
                                   ) -> docker.models.containers.Container:
    """
    Return the container which represents the given ``node``.
    """
    client = docker.from_env(version='auto')
    containers = client.containers.list()
    matching_containers = []
    for container in containers:
        networks = container.attrs['NetworkSettings']['Networks']
        for net in networks:
            if networks[net]['IPAddress'] == str(ip_addr):
                matching_containers.append(container)

    assert len(matching_containers) == 1
    return matching_containers[0]
